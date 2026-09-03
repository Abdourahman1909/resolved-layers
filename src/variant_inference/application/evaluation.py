from __future__ import annotations

import math

from variant_inference.application.ports import RunArchive, SourceDataset, SourceDatasetReader
from variant_inference.domain.models import (
    EvaluationCohort,
    EvaluationMetric,
    EvaluationReport,
    EvaluationSourceEvidence,
    GroundTruthAuthorization,
    LabelCoverage,
    LoadedVerifiedRun,
    SourceReferenceState,
    SourceReferenceStatus,
)


class EvaluationUnavailableError(RuntimeError):
    pass


class GroundTruthEvaluationService:
    """Calculate observed metrics only across checksum-valid, explicitly authorized labels."""

    def __init__(self, archive: RunArchive, reader: SourceDatasetReader) -> None:
        self._archive = archive
        self._reader = reader

    def prepare(self, run: LoadedVerifiedRun) -> EvaluationSourceEvidence:
        status = self._archive.source_status(run.run_id)
        if status.state is not SourceReferenceState.AVAILABLE:
            return self._unavailable_evidence(status)
        source = self._open_validated(run)
        try:
            return EvaluationSourceEvidence(
                state=SourceReferenceState.AVAILABLE,
                expected_sha256=run.source_sha256,
                current_sha256=source.identity.sha256,
                detail=(
                    "Original Source Dataset is checksum-valid. Select a label column and "
                    "authorize both raw class mappings; no candidate is selected automatically."
                ),
                # Expose the source schema without guessing which column is a label.
                # The operator must make the semantic choice explicitly.
                label_columns=source.columns,
            )
        finally:
            source.close()

    def label_values(self, run: LoadedVerifiedRun, column_name: str) -> tuple[str, ...]:
        source = self._open_validated(run)
        try:
            if column_name not in source.columns:
                raise ValueError(f"Source column {column_name!r} is not available.")
            return tuple(
                value
                for value, _ in source.value_counts(source.columns.index(column_name))
                if value
            )
        finally:
            source.close()

    def evaluate(
        self,
        run: LoadedVerifiedRun,
        authorization: GroundTruthAuthorization,
    ) -> EvaluationReport:
        source = self._open_validated(run)
        try:
            if authorization.column_name not in source.columns:
                raise ValueError(
                    f"Authorized label column {authorization.column_name!r} is absent."
                )
            (
                tp_rows,
                fp_rows,
                fn_rows,
                tn_rows,
                missing_rows,
                unrecognized_rows,
            ) = self._classified_rows(run, source, authorization)

            tp = len(tp_rows)
            fp = len(fp_rows)
            fn = len(fn_rows)
            tn = len(tn_rows)
            evaluated = tp + fp + fn + tn
            return EvaluationReport(
                run_id=run.run_id,
                source_sha256=run.source_sha256,
                authorization=authorization,
                total_records=len(run.predictions),
                evaluated_count=evaluated,
                missing_count=len(missing_rows),
                unrecognized_count=len(unrecognized_rows),
                true_positive=tp,
                false_positive=fp,
                false_negative=fn,
                true_negative=tn,
                metrics=self._metrics(tp, fp, fn, tn),
                cohorts=(
                    EvaluationCohort(
                        "false_positive",
                        "False positives",
                        "Predicted Pathogenic · authorized Ground Truth Benign",
                        tuple(fp_rows),
                    ),
                    EvaluationCohort(
                        "false_negative",
                        "False negatives",
                        "Predicted Benign · authorized Ground Truth Pathogenic",
                        tuple(fn_rows),
                    ),
                    EvaluationCohort(
                        "true_positive",
                        "True positives",
                        "Predicted Pathogenic · authorized Ground Truth Pathogenic",
                        tuple(tp_rows),
                    ),
                    EvaluationCohort(
                        "true_negative",
                        "True negatives",
                        "Predicted Benign · authorized Ground Truth Benign",
                        tuple(tn_rows),
                    ),
                ),
                missing_source_rows=tuple(missing_rows),
                unrecognized_source_rows=tuple(unrecognized_rows),
            )
        finally:
            source.close()

    def preview(
        self,
        run: LoadedVerifiedRun,
        proposed_mapping: GroundTruthAuthorization,
    ) -> LabelCoverage:
        """Return label coverage for operator review without calculating any metric."""
        source = self._open_validated(run)
        try:
            if proposed_mapping.column_name not in source.columns:
                raise ValueError(
                    f"Proposed label column {proposed_mapping.column_name!r} is absent."
                )
            classified = self._classified_rows(run, source, proposed_mapping)
            pathogenic = len(classified[0]) + len(classified[2])
            benign = len(classified[1]) + len(classified[3])
            return LabelCoverage(
                total=len(run.predictions),
                pathogenic=pathogenic,
                benign=benign,
                missing=len(classified[4]),
                unrecognized=len(classified[5]),
            )
        finally:
            source.close()

    @staticmethod
    def _classified_rows(
        run: LoadedVerifiedRun,
        source: SourceDataset,
        mapping: GroundTruthAuthorization,
    ) -> tuple[list[int], list[int], list[int], list[int], list[int], list[int]]:
        label_index = source.columns.index(mapping.column_name)
        tp_rows: list[int] = []
        fp_rows: list[int] = []
        fn_rows: list[int] = []
        tn_rows: list[int] = []
        missing_rows: list[int] = []
        unrecognized_rows: list[int] = []
        for record in run.predictions:
            raw_label = source.row_at(record.source_row - 1)[label_index]
            if not raw_label.strip():
                missing_rows.append(record.source_row)
            elif raw_label == mapping.pathogenic_value:
                (tp_rows if record.prediction == "Pathogenic" else fn_rows).append(
                    record.source_row
                )
            elif raw_label == mapping.benign_value:
                (fp_rows if record.prediction == "Pathogenic" else tn_rows).append(
                    record.source_row
                )
            else:
                unrecognized_rows.append(record.source_row)
        return tp_rows, fp_rows, fn_rows, tn_rows, missing_rows, unrecognized_rows

    def _open_validated(self, run: LoadedVerifiedRun) -> SourceDataset:
        status = self._archive.source_status(run.run_id)
        if status.state is not SourceReferenceState.AVAILABLE:
            raise EvaluationUnavailableError(
                "Evaluation requires the original Source Dataset to remain checksum-valid."
            )
        signature_before = self._file_signature(run.source_path)
        if signature_before is None:
            raise EvaluationUnavailableError(
                "The checksum-valid Source Dataset disappeared before Evaluation could open it."
            )
        try:
            source = self._reader.open(run.source_path)
        except (OSError, ValueError) as error:
            raise EvaluationUnavailableError(
                "The checksum-valid Source Dataset could not be opened for Evaluation."
            ) from error
        signature_after = self._file_signature(run.source_path)
        if signature_before != signature_after:
            source.close()
            raise EvaluationUnavailableError(
                "The Source Dataset changed while Evaluation was opening it. "
                "Refresh and re-authorize against stable source evidence."
            )
        if (
            source.identity.sha256 != run.source_sha256
            or source.identity.row_count != run.source_row_count
            or source.identity.column_count != run.source_column_count
        ):
            source.close()
            raise EvaluationUnavailableError(
                "Evaluation requires the exact checksum-valid Source Dataset and dimensions."
            )
        return source

    @staticmethod
    def _file_signature(path) -> tuple[int, int, int, int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return (
            int(stat.st_dev),
            int(stat.st_ino),
            int(stat.st_size),
            int(stat.st_mtime_ns),
            int(stat.st_ctime_ns),
        )

    @staticmethod
    def _metrics(tp: int, fp: int, fn: int, tn: int) -> tuple[EvaluationMetric, ...]:
        f1_denominator = 2 * tp + fp + fn
        precision_denominator = tp + fp
        recall_denominator = tp + fn
        accuracy_denominator = tp + fp + fn + tn
        mcc_product = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        mcc_denominator = math.sqrt(mcc_product)

        def ratio(numerator: float, denominator: float) -> float | None:
            return numerator / denominator if denominator else None

        return (
            EvaluationMetric(
                "f1",
                "F1",
                ratio(2 * tp, f1_denominator),
                f1_denominator,
                "2TP / (2TP + FP + FN)",
            ),
            EvaluationMetric(
                "precision",
                "Precision",
                ratio(tp, precision_denominator),
                precision_denominator,
                "TP / (TP + FP)",
            ),
            EvaluationMetric(
                "recall",
                "Recall",
                ratio(tp, recall_denominator),
                recall_denominator,
                "TP / (TP + FN)",
            ),
            EvaluationMetric(
                "mcc",
                "MCC",
                ratio(tp * tn - fp * fn, mcc_denominator),
                mcc_denominator,
                "(TP×TN − FP×FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN))",
            ),
            EvaluationMetric(
                "accuracy",
                "Accuracy",
                ratio(tp + tn, accuracy_denominator),
                accuracy_denominator,
                "(TP + TN) / Evaluated Cohort",
            ),
        )

    @staticmethod
    def _unavailable_evidence(status: SourceReferenceStatus) -> EvaluationSourceEvidence:
        if status.state is SourceReferenceState.MISSING:
            detail = (
                "Original Source Dataset is missing at its archived path. Evaluation is disabled."
            )
        else:
            detail = (
                "Original Source Dataset checksum differs from the Verified Run. Evaluation is disabled."
            )
        return EvaluationSourceEvidence(
            state=status.state,
            expected_sha256=status.expected_sha256,
            current_sha256=status.current_sha256,
            detail=detail,
        )

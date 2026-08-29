from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from variant_inference.application.ports import DeterministicInference, RunArchive, SourceDataset
from variant_inference.domain.models import (
    ArchivedRun,
    ContractFit,
    ModelPackageIdentity,
    PredictionRecord,
    TransformationAudit,
    VerifiedRun,
)


class VerifiedRunError(RuntimeError):
    pass


def canonical_prediction_payload(records: tuple[PredictionRecord, ...]) -> bytes:
    lines = []
    for record in records:
        lines.append(
            json.dumps(
                {
                    "component_scores": dict(record.component_scores),
                    "ensemble_score": record.ensemble_score,
                    "model_disagreement": record.model_disagreement,
                    "prediction": record.prediction,
                    "source_row": record.source_row,
                },
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")


class VerifiedRunService:
    def __init__(
        self,
        inference: DeterministicInference,
        archive: RunArchive,
        *,
        clock: Callable[[], datetime] | None = None,
        timer: Callable[[], float] | None = None,
        run_id_factory: Callable[[datetime], str] | None = None,
    ) -> None:
        self._inference = inference
        self._archive = archive
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timer = timer or time.perf_counter
        self._run_id_factory = run_id_factory or self._default_run_id

    def execute(
        self,
        *,
        source: SourceDataset,
        package: ModelPackageIdentity,
        fit: ContractFit,
        audit: TransformationAudit,
        operator_confirmed: bool,
    ) -> ArchivedRun:
        if not operator_confirmed:
            raise VerifiedRunError("Source Review confirmation is required before prediction.")
        if not fit.is_compatible:
            raise VerifiedRunError("Blocking Inference Contract findings prevent prediction.")

        created_at = self._clock()
        started = self._timer()
        predictions = tuple(self._inference.predict(source, package))
        duration_ms = max(0, round((self._timer() - started) * 1000))
        completed_at = self._clock()
        expected_rows = tuple(range(1, source.identity.row_count + 1))
        actual_rows = tuple(record.source_row for record in predictions)
        if actual_rows != expected_rows:
            raise VerifiedRunError(
                "Inference output did not preserve every Source Row in deterministic order."
            )

        payload = canonical_prediction_payload(predictions)
        run = VerifiedRun(
            run_id=self._run_id_factory(created_at),
            created_at=created_at.astimezone(timezone.utc).isoformat(timespec="milliseconds"),
            completed_at=completed_at.astimezone(timezone.utc).isoformat(timespec="milliseconds"),
            duration_ms=duration_ms,
            source=source.identity,
            model_package_id=package.package_id,
            model_package_name=package.display_name,
            model_package_version=package.version,
            model_package_manifest_checksum=package.manifest_checksum,
            inference_contract_id=package.contract.contract_id,
            inference_contract_version=package.contract.version,
            inference_contract_checksum=package.contract.checksum,
            release_threshold=package.contract.release_threshold,
            predictions=predictions,
            predictions_sha256=hashlib.sha256(payload).hexdigest(),
            warnings=fit.warnings,
            transformation_audit=audit,
        )
        return self._archive.save(run)

    @staticmethod
    def _default_run_id(created_at: datetime) -> str:
        stamp = created_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        return f"run-{stamp}-{uuid.uuid4().hex[:12]}"

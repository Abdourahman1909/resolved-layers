"""Write the official TEKNOFEST submission file for a Verified Run.

The format is fixed by the organisers' final application guide, `TEKNOFEST 2026
Sağlıkta Yapay Zekâ — Final Uygulama, Model Testi ve Sonuç Teslim Kılavuzu`,
section 3.2. Nothing here is inferred: every field name, class value and rule
below is taken from that document, and the profile records which version of it
was followed.

The submission is the only artefact that counts. After the upload window closes
the organisers accept no result by email, USB or message, and a file the upload
system rejects is not a submission at all. This module therefore validates
against every stated rule before writing, and refuses rather than writing a file
that would be rejected on arrival.

The uploaded file is scored automatically, so a malformed submission is a zero
regardless of how good the model is.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from variant_inference.application.ports import SourceDatasetReader
from variant_inference.domain.models import LoadedVerifiedRun


class CompetitionExportError(RuntimeError):
    """The submission could not be produced, or would have been invalid."""


@dataclass(frozen=True)
class CompetitionExportProfile:
    """One published organiser format.

    Versioned deliberately. When the organisers revise the guide, a new profile
    is added rather than this one edited, so a submission can always state which
    published format it followed.
    """

    profile_id: str = "teknofest-2026-final-v1"
    source_document: str = (
        "TEKNOFEST 2026 Sağlıkta Yapay Zekâ — Final Uygulama, "
        "Model Testi ve Sonuç Teslim Kılavuzu, section 3.2"
    )
    competition_level: str = "UNIVERSITE_VE_UZERI"
    pathogenic_class: str = "1"
    benign_class: str = "0"
    file_name_template: str = "TEAM_{team_id}_FINAL.json"
    # Probabilities are used for AUROC-style metrics and the PR-AUC tie-break,
    # so they are written at full precision rather than rounded for display.
    probability_digits: int = 12

    @property
    def valid_classes(self) -> tuple[str, ...]:
        return (self.benign_class, self.pathogenic_class)


@dataclass(frozen=True)
class CompetitionTeam:
    """Team identity exactly as registered in the organisers' system (KYS)."""

    team_name: str
    team_id: str
    application_id: str

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("team name", self.team_name),
                ("team id", self.team_id),
                ("application id", self.application_id),
            )
            if not value.strip()
        ]
        if missing:
            raise CompetitionExportError(
                "The submission header needs " + ", ".join(missing) +
                ". These must match the registered details exactly."
            )


@dataclass(frozen=True)
class CompetitionExportReport:
    path: Path
    record_count: int
    pathogenic_count: int
    benign_count: int
    identifier_column: str
    panel_column: str
    profile_id: str
    checks: tuple[str, ...] = field(default_factory=tuple)


class CompetitionExportService:
    """Join immutable predictions to their source identifiers and write JSON."""

    def __init__(
        self,
        reader: SourceDatasetReader,
        profile: CompetitionExportProfile | None = None,
    ) -> None:
        self._reader = reader
        self._profile = profile or CompetitionExportProfile()

    @property
    def profile(self) -> CompetitionExportProfile:
        return self._profile

    def suggested_file_name(self, team: CompetitionTeam) -> str:
        return self._profile.file_name_template.format(team_id=team.team_id or "UNKNOWN")

    def export(
        self,
        run: LoadedVerifiedRun,
        destination: Path,
        team: CompetitionTeam,
        identifier_column: str,
        panel_column: str,
    ) -> CompetitionExportReport:
        team.validate()
        destination = Path(destination)
        if destination.suffix.lower() != ".json":
            destination = destination.with_suffix(".json")

        source = self._open_verified_source(run)
        try:
            predictions, checks = self._build(
                run, source, identifier_column, panel_column
            )
        finally:
            source.close()

        payload = {
            "team_name": team.team_name,
            "team_id": team.team_id,
            "application_id": team.application_id,
            "competition_level": self._profile.competition_level,
            "predictions": predictions,
        }
        self._write(destination, payload)

        pathogenic = sum(
            1
            for item in predictions
            if item["predicted_class"] == self._profile.pathogenic_class
        )
        return CompetitionExportReport(
            path=destination,
            record_count=len(predictions),
            pathogenic_count=pathogenic,
            benign_count=len(predictions) - pathogenic,
            identifier_column=identifier_column,
            panel_column=panel_column,
            profile_id=self._profile.profile_id,
            checks=checks,
        )

    # Source access --------------------------------------------------------

    def _open_verified_source(self, run: LoadedVerifiedRun):
        if not run.source_path.is_file():
            raise CompetitionExportError(
                "The original Source Dataset is missing, so record identifiers "
                "cannot be recovered."
            )
        if self._checksum(run.source_path) != run.source_sha256:
            raise CompetitionExportError(
                "The original Source Dataset has changed since this run. Its "
                "identifiers can no longer be attributed to these predictions."
            )
        try:
            source = self._reader.open(run.source_path)
        except (OSError, ValueError) as error:
            raise CompetitionExportError(
                "The original Source Dataset could not be opened."
            ) from error
        if len(source.columns) != run.source_column_count:
            source.close()
            raise CompetitionExportError(
                "The original Source Dataset no longer has the dimensions "
                "recorded for this run."
            )
        return source

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    # Building -------------------------------------------------------------

    def _build(
        self,
        run: LoadedVerifiedRun,
        source,
        identifier_column: str,
        panel_column: str,
    ) -> tuple[list[dict], tuple[str, ...]]:
        for name, column in (
            ("identifier", identifier_column),
            ("panel", panel_column),
        ):
            if column not in source.columns:
                raise CompetitionExportError(
                    f"The chosen {name} column {column!r} is not in the Source Dataset."
                )
        id_index = source.columns.index(identifier_column)
        panel_index = source.columns.index(panel_column)

        predictions: list[dict] = []
        seen: set[str] = set()
        # Uniqueness is checked on the identifier together with its panel, not
        # on the identifier alone. The organisers' own data repeats an
        # identifier across panels while never repeating it inside one, and
        # every submitted record carries both fields, so the pair is what
        # identifies a record. Refusing on the identifier alone would have
        # blocked a legitimate submission on a file shaped like theirs.
        seen_pairs: set[tuple[str, str]] = set()
        repeated_across_panels: set[str] = set()
        blank_panels = 0
        for record in run.predictions:
            row = source.row_at(record.source_row - 1)

            identifier = row[id_index].strip()
            if not identifier:
                raise CompetitionExportError(
                    f"Source Row {record.source_row} has an empty "
                    f"{identifier_column!r}. Every test record needs an identifier, "
                    "and identifiers must not be invented."
                )
            panel_value = row[panel_index].strip()
            if (identifier, panel_value) in seen_pairs:
                raise CompetitionExportError(
                    f"Identifier {identifier!r} appears more than once in panel "
                    f"{panel_value!r}. That is the same record twice, which the "
                    "organisers reject."
                )
            if identifier in seen:
                # Legitimate in their data. Disclosed, never silently altered:
                # a modified identifier would not match their ground truth.
                repeated_across_panels.add(identifier)
            seen_pairs.add((identifier, panel_value))
            seen.add(identifier)

            probability = float(record.ensemble_score)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise CompetitionExportError(
                    f"Source Row {record.source_row} has a probability that is "
                    "not a finite value between 0 and 1."
                )

            if not panel_value:
                blank_panels += 1

            predictions.append(
                {
                    "id": identifier,
                    "panel": panel_value,
                    "predicted_class": (
                        self._profile.pathogenic_class
                        if record.prediction == "Pathogenic"
                        else self._profile.benign_class
                    ),
                    "predicted_prob": round(probability, self._profile.probability_digits),
                }
            )

        if len(predictions) != len(run.predictions):
            raise CompetitionExportError(
                "Every prediction must appear exactly once in the submission."
            )

        checks = [
            f"{len(predictions)} records, one per Source Row",
            f"{len(seen_pairs)} unique identifier and panel pairs from "
            f"{identifier_column!r} and {panel_column!r}",
            "every probability finite and within 0 to 1",
            f"classes limited to {self._profile.valid_classes}",
        ]
        if repeated_across_panels:
            # Worth reading before uploading: it is what their data does, but it
            # is also what a wrong identifier column would look like.
            checks.append(
                f"{len(repeated_across_panels)} identifiers appear in more than "
                "one panel, as the organisers' own data does; each is unique "
                "within its panel and is written exactly as given"
            )
        if blank_panels:
            # Not fatal: the guide fixes the class names but not the panel values.
            checks.append(f"{blank_panels} records have an empty panel value")
        return predictions, tuple(checks)

    # Writing --------------------------------------------------------------

    def _write(self, destination: Path, payload: dict) -> None:
        # allow_nan=False makes json refuse NaN and Infinity rather than emitting
        # the non-standard literals the organisers reject.
        try:
            text = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2)
        except ValueError as error:
            raise CompetitionExportError(
                f"The submission contained a value JSON cannot represent: {error}"
            ) from error

        # Parse it back before it reaches disk: a file the upload system cannot
        # read is not a submission, and there is no second chance after the
        # window closes.
        json.loads(text)

        destination.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(
            dir=str(destination.parent), prefix=destination.name, suffix=".tmp"
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(text + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

from __future__ import annotations

from dataclasses import dataclass

from variant_inference.domain.models import (
    InvestigationSet,
    LoadedVerifiedRun,
    PredictionRecord,
    ScoreBin,
)


@dataclass
class ResultSetSession:
    run: LoadedVerifiedRun | None = None
    selection_key: str = "all"
    selection_title: str = "All predictions"
    selected_lower: float = 0.0
    selected_upper: float = 1.0
    selected_source_rows: tuple[int, ...] = ()

    BIN_COUNT = 32
    NEAR_THRESHOLD_RADIUS = 0.06

    def clear(self) -> None:
        """Forget the loaded run, for when it is removed from the archive."""
        self.run = None
        self.selection_key = "all"
        self.selection_title = "All predictions"
        self.selected_lower = 0.0
        self.selected_upper = 1.0
        self.selected_source_rows = ()

    def load(self, run: LoadedVerifiedRun) -> None:
        self.run = run
        self.selected_source_rows = ()
        lower = max(0.0, run.release_threshold - self.NEAR_THRESHOLD_RADIUS)
        upper = min(1.0, run.release_threshold + self.NEAR_THRESHOLD_RADIUS)
        self.select_score_range(lower, upper, "Near release threshold")

    @property
    def predictions(self) -> tuple[PredictionRecord, ...]:
        return self.run.predictions if self.run else ()

    @property
    def pathogenic_count(self) -> int:
        return sum(record.prediction == "Pathogenic" for record in self.predictions)

    @property
    def benign_count(self) -> int:
        return len(self.predictions) - self.pathogenic_count

    @property
    def component_conflict_count(self) -> int:
        return sum(self._component_conflict(record) for record in self.predictions)

    @property
    def score_bins(self) -> tuple[ScoreBin, ...]:
        counts = [0] * self.BIN_COUNT
        for record in self.predictions:
            index = min(self.BIN_COUNT - 1, int(record.ensemble_score * self.BIN_COUNT))
            counts[index] += 1
        width = 1.0 / self.BIN_COUNT
        return tuple(
            ScoreBin(index * width, (index + 1) * width, count)
            for index, count in enumerate(counts)
        )

    @property
    def investigation_sets(self) -> tuple[InvestigationSet, ...]:
        if self.run is None:
            return ()
        near_lower = max(0.0, self.run.release_threshold - self.NEAR_THRESHOLD_RADIUS)
        near_upper = min(1.0, self.run.release_threshold + self.NEAR_THRESHOLD_RADIUS)
        return (
            InvestigationSet(
                "near_threshold",
                "Near release threshold",
                f"Scores from {near_lower:.2f} to {near_upper:.2f}",
                self._count_score_range(near_lower, near_upper),
            ),
            InvestigationSet(
                "component_conflict",
                "Component decision conflicts",
                "CatBoost and LightGBM fall on opposite sides",
                self.component_conflict_count,
            ),
            InvestigationSet(
                "pathogenic",
                "Predicted Pathogenic",
                f"Scores at or above {self.run.release_threshold:.2f}",
                self.pathogenic_count,
            ),
            InvestigationSet(
                "benign",
                "Predicted Benign",
                f"Scores below {self.run.release_threshold:.2f}",
                self.benign_count,
            ),
        )

    @property
    def selected_records(self) -> tuple[PredictionRecord, ...]:
        if self.run is None:
            return ()
        if self.selection_key in {"near_threshold", "score_range"}:
            return tuple(
                record
                for record in self.predictions
                if self.selected_lower <= record.ensemble_score <= self.selected_upper
            )
        if self.selection_key == "component_conflict":
            return tuple(record for record in self.predictions if self._component_conflict(record))
        if self.selection_key == "pathogenic":
            return tuple(record for record in self.predictions if record.prediction == "Pathogenic")
        if self.selection_key == "benign":
            return tuple(record for record in self.predictions if record.prediction == "Benign")
        if self.selection_key == "evaluation_cohort":
            selected = set(self.selected_source_rows)
            return tuple(record for record in self.predictions if record.source_row in selected)
        return self.predictions

    def select_investigation_set(self, key: str) -> None:
        if self.run is None:
            return
        if key == "near_threshold":
            self.select_score_range(
                max(0.0, self.run.release_threshold - self.NEAR_THRESHOLD_RADIUS),
                min(1.0, self.run.release_threshold + self.NEAR_THRESHOLD_RADIUS),
                "Near release threshold",
            )
            return
        match = next((item for item in self.investigation_sets if item.key == key), None)
        if match is None:
            raise ValueError(f"Unknown Investigation Set: {key}")
        self.selection_key = key
        self.selection_title = match.title
        self.selected_lower = 0.0
        self.selected_upper = 1.0

    def select_score_range(self, lower: float, upper: float, title: str = "Selected score range") -> None:
        if not 0.0 <= lower <= upper <= 1.0:
            raise ValueError("Score selection must remain between zero and one.")
        self.selection_key = "score_range"
        self.selection_title = title
        self.selected_lower = lower
        self.selected_upper = upper

    def clear_selection(self) -> None:
        self.selection_key = "all"
        self.selection_title = "All predictions"
        self.selected_lower = 0.0
        self.selected_upper = 1.0
        self.selected_source_rows = ()

    def select_source_rows(self, source_rows: tuple[int, ...], title: str) -> None:
        if self.run is None:
            raise ValueError("A Verified Run must be loaded before selecting records.")
        available = {record.source_row for record in self.predictions}
        requested = set(source_rows)
        invalid = requested - available
        if invalid:
            raise ValueError("Evaluation cohort contains Source Rows outside the immutable Result Set.")
        self.selection_key = "evaluation_cohort"
        self.selection_title = title
        self.selected_lower = 0.0
        self.selected_upper = 1.0
        self.selected_source_rows = tuple(
            record.source_row for record in self.predictions if record.source_row in requested
        )

    def _component_conflict(self, record: PredictionRecord) -> bool:
        if self.run is None or not record.component_scores:
            return False
        decisions = {
            score >= self.run.release_threshold
            for score in record.component_scores.values()
        }
        return len(decisions) > 1

    def _count_score_range(self, lower: float, upper: float) -> int:
        return sum(lower <= record.ensemble_score <= upper for record in self.predictions)

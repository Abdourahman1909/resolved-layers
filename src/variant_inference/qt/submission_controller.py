"""Expose Competition Submission to QML.

QML chooses two columns and a destination, and reads back what was checked.
Reading identifiers, hashing the source and writing the file happen off the QML
thread, because the final data may be large and the interface must stay
responsive while the clock is running.

The controller reports the validation outcome even when nothing is written.
Discovering that a submission would be rejected is the point of running the
checks; it is more useful before the upload window closes than after.
"""

from __future__ import annotations

import os
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from variant_inference.application.competition_export import (
    CompetitionExportError,
    CompetitionExportService,
    CompetitionTeam,
)

# Registered identity, as recorded in the organisers' system. These are
# registration identifiers rather than restricted competition material. Each can
# be overridden without a rebuild, so a correction on the day needs no developer.
DEFAULT_TEAM = CompetitionTeam(
    team_name=os.environ.get("CHL_TEAM_NAME", "Computational-Health-Lab"),
    team_id=os.environ.get("CHL_TEAM_ID", "763095"),
    application_id=os.environ.get("CHL_APPLICATION_ID", "4484264"),
)

# Columns tried first when a run is opened. The operator can always override,
# because the final data may name them differently and a wrong choice produces
# a rejected submission.
IDENTIFIER_CANDIDATES = ("Variant_ID", "variant_id", "VariantID", "Varyant_ID", "id", "ID")
PANEL_CANDIDATES = ("_panel", "panel", "Panel", "PANEL")


class SubmissionController(QObject):
    stateChanged = Signal()
    exportFinished = Signal()

    def __init__(
        self,
        service: CompetitionExportService,
        results_controller,
        team: CompetitionTeam | None = None,
        executor: Executor | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._results = results_controller
        self._team = team or DEFAULT_TEAM
        self._owns_executor = executor is None
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="resolved-layers-submission"
        )
        self._identifier_column = ""
        self._panel_column = ""
        self._columns: tuple[str, ...] = ()
        self._busy = False
        self._checks: list[str] = []
        self._message = "Open a Verified Run to prepare the submission."
        self._message_kind = "neutral"
        self._written_path = ""
        self._request_id = 0
        self._run_id = ""

        self.exportFinished.connect(self._emit)
        changed = getattr(results_controller, "stateChanged", None)
        if changed is not None:
            changed.connect(self._follow_run)

    def _emit(self) -> None:
        self.stateChanged.emit()

    # Run tracking ---------------------------------------------------------

    def _follow_run(self) -> None:
        """Reset when a different run is opened, and propose likely columns."""
        run = self._results.current_run
        run_id = run.run_id if run else ""
        if run_id == self._run_id:
            return
        self._run_id = run_id
        self._checks = []
        self._written_path = ""
        self._identifier_column = ""
        self._panel_column = ""
        self._columns = ()

        if run is None:
            self._message = "Open a Verified Run to prepare the submission."
            self._message_kind = "neutral"
            self._emit()
            return

        self._columns = self._source_columns(run)
        self._identifier_column = self._propose(IDENTIFIER_CANDIDATES)
        self._panel_column = self._propose(PANEL_CANDIDATES)
        if self._identifier_column:
            self._message = "Confirm the identifier and panel columns, then write the submission."
            self._message_kind = "neutral"
        else:
            # Identifiers are never invented; the operator must name the column.
            self._message = (
                "No familiar identifier column was found. Choose the column holding "
                "the organisers' record identifiers."
            )
            self._message_kind = "warning"
        self._emit()

    def _source_columns(self, run) -> tuple[str, ...]:
        try:
            source = self._service._reader.open(run.source_path)  # noqa: SLF001
        except Exception:
            return ()
        try:
            return tuple(source.columns)
        finally:
            source.close()

    def _propose(self, candidates: tuple[str, ...]) -> str:
        for candidate in candidates:
            if candidate in self._columns:
                return candidate
        return ""

    # Operator choices -----------------------------------------------------

    @Slot(str)
    def selectIdentifierColumn(self, column_name: str) -> None:  # noqa: N802
        if self._busy or (column_name and column_name not in self._columns):
            return
        self._identifier_column = column_name
        self._checks = []
        self._written_path = ""
        self._emit()

    @Slot(str)
    def selectPanelColumn(self, column_name: str) -> None:  # noqa: N802
        if self._busy or (column_name and column_name not in self._columns):
            return
        self._panel_column = column_name
        self._checks = []
        self._written_path = ""
        self._emit()

    @Slot(str)
    def writeSubmission(self, value: str) -> None:  # noqa: N802
        run = self._results.current_run
        if run is None or self._busy or not self.canWrite:
            return

        url = QUrl(value)
        destination = Path(url.toLocalFile() if url.isLocalFile() else value)

        self._request_id += 1
        request_id = self._request_id
        self._busy = True
        self._checks = []
        self._message = "Checking the submission against the organisers' rules…"
        self._message_kind = "neutral"
        self._emit()

        future = self._executor.submit(
            self._service.export,
            run,
            destination,
            self._team,
            self._identifier_column,
            self._panel_column,
        )
        future.add_done_callback(lambda done: self._finish(done, request_id))

    def _finish(self, done: Future, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._busy = False
        try:
            report = done.result()
        except CompetitionExportError as error:
            # Fail closed and name the rule that was broken, while there is
            # still time to correct it.
            self._written_path = ""
            self._checks = []
            self._message = str(error)
            self._message_kind = "error"
            self.exportFinished.emit()
            return
        except Exception as error:  # defensive: never leave the UI stuck busy
            self._written_path = ""
            self._checks = []
            self._message = f"The submission could not be written. {error}"
            self._message_kind = "error"
            self.exportFinished.emit()
            return

        self._written_path = str(report.path)
        self._checks = list(report.checks)
        self._message = (
            f"Submission written: {report.record_count:,} records, "
            f"{report.pathogenic_count:,} Pathogenic and {report.benign_count:,} Benign."
        )
        self._message_kind = "success"
        self.exportFinished.emit()

    # Evidence -------------------------------------------------------------

    @Property(bool, notify=stateChanged)
    def hasRun(self) -> bool:  # noqa: N802
        return self._results.current_run is not None

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def canWrite(self) -> bool:  # noqa: N802
        return bool(
            self._results.current_run is not None
            and self._identifier_column
            and self._panel_column
            and not self._busy
        )

    @Property("QStringList", notify=stateChanged)
    def sourceColumns(self) -> list[str]:  # noqa: N802
        return list(self._columns)

    @Property(str, notify=stateChanged)
    def identifierColumn(self) -> str:  # noqa: N802
        return self._identifier_column

    @Property(str, notify=stateChanged)
    def panelColumn(self) -> str:  # noqa: N802
        return self._panel_column

    @Property("QStringList", notify=stateChanged)
    def checks(self) -> list[str]:
        return list(self._checks)

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def messageKind(self) -> str:  # noqa: N802
        return self._message_kind

    @Property(str, notify=stateChanged)
    def writtenPath(self) -> str:  # noqa: N802
        return self._written_path

    @Property(str, constant=True)
    def teamName(self) -> str:  # noqa: N802
        return self._team.team_name

    @Property(str, constant=True)
    def teamId(self) -> str:  # noqa: N802
        return self._team.team_id

    @Property(str, constant=True)
    def applicationId(self) -> str:  # noqa: N802
        return self._team.application_id

    @Property(str, constant=True)
    def competitionLevel(self) -> str:  # noqa: N802
        return self._service.profile.competition_level

    @Property(str, constant=True)
    def profileId(self) -> str:  # noqa: N802
        return self._service.profile.profile_id

    @Property(str, constant=True)
    def suggestedFileName(self) -> str:  # noqa: N802
        return self._service.suggested_file_name(self._team)

    @Property(int, notify=stateChanged)
    def recordCount(self) -> int:  # noqa: N802
        run = self._results.current_run
        return len(run.predictions) if run else 0

    def shutdown(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

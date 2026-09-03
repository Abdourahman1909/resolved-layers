"""Expose Research Export to QML.

QML chooses a destination and reports the outcome. Reading the source, hashing
it, and writing the file happen off the QML thread, because a large cohort can
take noticeable time and the interface must not freeze while it does.
"""

from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from variant_inference.application.research_export import (
    ResearchExportError,
    ResearchExportService,
)


class ExportController(QObject):
    stateChanged = Signal()
    exportFinished = Signal()

    def __init__(
        self,
        service: ResearchExportService,
        results_controller,
        executor: Executor | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._results = results_controller
        self._owns_executor = executor is None
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="resolved-layers-export"
        )
        self._busy = False
        self._message = ""
        self._message_kind = "neutral"
        self._last_path = ""
        self._request_id = 0
        self.exportFinished.connect(self._emit)
        # canExport and suggestedFileName both read the results controller, so
        # they must be re-evaluated when a run is opened or replaced. Without
        # this the export action stays disabled after a run loads.
        results_changed = getattr(results_controller, "stateChanged", None)
        if results_changed is not None:
            results_changed.connect(self._emit)

    def _emit(self) -> None:
        self.stateChanged.emit()

    @Slot(str)
    def exportResearchCsv(self, value: str) -> None:  # noqa: N802
        run = self._results.current_run
        if run is None:
            self._report("Open a Verified Run before exporting.", "error")
            return
        if self._busy:
            return

        url = QUrl(value)
        destination = Path(url.toLocalFile() if url.isLocalFile() else value)

        self._request_id += 1
        request_id = self._request_id
        self._busy = True
        self._message = "Writing export…"
        self._message_kind = "neutral"
        self._emit()

        future = self._executor.submit(self._service.export, run, destination)
        future.add_done_callback(lambda done: self._finish(done, request_id))

    def _finish(self, done: Future, request_id: int) -> None:
        if request_id != self._request_id:
            return  # superseded by a newer export
        self._busy = False
        try:
            report = done.result()
        except ResearchExportError as error:
            # Fail closed and say why, rather than leaving a half-truth on screen.
            self._last_path = ""
            self._report(str(error), "error")
            return
        except Exception as error:  # defensive: never leave the UI stuck busy
            self._last_path = ""
            self._report(f"The export could not be written. {error}", "error")
            return

        self._last_path = str(report.csv_path)
        self._report(
            f"Exported {report.row_count} records and "
            f"{report.source_column_count} source columns to {report.csv_path.name}, "
            f"with evidence in {report.evidence_path.name}.",
            "success",
        )

    def _report(self, message: str, kind: str) -> None:
        self._message = message
        self._message_kind = kind
        self.exportFinished.emit()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def canExport(self) -> bool:  # noqa: N802
        return self._results.current_run is not None and not self._busy

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def messageKind(self) -> str:  # noqa: N802
        return self._message_kind

    @Property(str, notify=stateChanged)
    def lastExportPath(self) -> str:  # noqa: N802
        return self._last_path

    @Property(str, notify=stateChanged)
    def suggestedFileName(self) -> str:  # noqa: N802
        run = self._results.current_run
        if run is None:
            return "resolved-layers-export.csv"
        stem = Path(run.source_file_name).stem or "source"
        return f"{stem}-predictions.csv"

    def shutdown(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

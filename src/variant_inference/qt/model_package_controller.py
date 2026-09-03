"""Expose Model Package installation to QML.

QML chooses a folder and displays evidence. It never parses a manifest, hashes
an artifact, or decides trust; those stay in the application service. Package
validation reads and hashes files from disk, so it runs off the QML thread.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from variant_inference.application.model_package_settings import (
    ModelPackageInstallationService,
)
from variant_inference.domain.models import ModelPackageCandidate, ModelPackageTrust


class ModelPackageController(QObject):
    stateChanged = Signal()
    installedChanged = Signal()

    def __init__(self, service: ModelPackageInstallationService) -> None:
        super().__init__()
        self._service = service
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="model-package")
        self._candidate: ModelPackageCandidate | None = None
        self._installed: ModelPackageCandidate | None = None
        self._busy = False
        self._message = "No Model Package installed."
        self._message_kind = "neutral"
        self._pending: Future | None = None

    # Startup --------------------------------------------------------------

    def refresh_installed(self) -> None:
        """Revalidate the configured package. Safe to call before QML loads."""
        self._installed = self._service.configured()
        self._describe_installed()
        self.installedChanged.emit()
        self.stateChanged.emit()

    def _describe_installed(self) -> None:
        installed = self._installed
        if installed is None:
            self._message = "No Model Package installed."
            self._message_kind = "neutral"
        elif installed.is_usable:
            self._message = "Model Package ready."
            self._message_kind = "success"
        elif installed.trust is ModelPackageTrust.INVALID:
            # Fail closed and say why. The package moved, changed, or an
            # artifact no longer matches its declared checksum.
            self._message = f"Installed Model Package is unusable. {installed.problem}"
            self._message_kind = "error"
        else:
            self._message = "Installed Model Package is no longer confirmed."
            self._message_kind = "error"

    # Selection ------------------------------------------------------------

    @Slot(str)
    def selectPackage(self, value: str) -> None:  # noqa: N802
        url = QUrl(value)
        path = Path(url.toLocalFile() if url.isLocalFile() else value)
        self._busy = True
        self._message = "Validating Model Package…"
        self._message_kind = "neutral"
        self.stateChanged.emit()

        future = self._executor.submit(self._service.inspect, path)
        self._pending = future
        future.add_done_callback(lambda done: self._finish_inspection(done, future))

    def _finish_inspection(self, done: Future, expected: Future) -> None:
        if self._pending is not expected:
            return  # a newer selection superseded this one
        self._busy = False
        self._pending = None
        try:
            candidate = done.result()
        except Exception as error:  # defensive: surface rather than crash the UI
            self._candidate = None
            self._message = f"Could not read that Model Package. {error}"
            self._message_kind = "error"
            self.stateChanged.emit()
            return

        self._candidate = candidate
        if candidate.trust is ModelPackageTrust.INVALID:
            self._message = candidate.problem
            self._message_kind = "error"
        elif candidate.needs_confirmation:
            self._message = "Review this package and confirm its checksum to trust it."
            self._message_kind = "warning"
        elif candidate.trust is ModelPackageTrust.OFFICIAL:
            self._message = "Recognised official Model Package."
            self._message_kind = "success"
        else:
            self._message = "Previously confirmed Model Package."
            self._message_kind = "success"
        self.stateChanged.emit()

    @Slot()
    def confirmSelected(self) -> None:  # noqa: N802
        """Vouch for the selected package's exact manifest checksum."""
        candidate = self._candidate
        if candidate is None or not candidate.needs_confirmation:
            return
        self._candidate = self._service.confirm(candidate)
        self._message = "Checksum confirmed. Install it to use it at startup."
        self._message_kind = "success"
        self.stateChanged.emit()

    @Slot()
    def installSelected(self) -> None:  # noqa: N802
        candidate = self._candidate
        if candidate is None or not candidate.is_usable:
            return
        self._installed = self._service.install(candidate)
        self._message = "Model Package installed. Restart to use it for prediction."
        self._message_kind = "success"
        self.installedChanged.emit()
        self.stateChanged.emit()

    @Slot()
    def removeInstalled(self) -> None:  # noqa: N802
        self._service.remove()
        self._installed = None
        self._message = "Model Package removed. Restart to apply."
        self._message_kind = "neutral"
        self.installedChanged.emit()
        self.stateChanged.emit()

    # Evidence -------------------------------------------------------------

    def _selected_field(self, reader, default: str = "—") -> str:
        candidate = self._candidate
        if candidate is None or candidate.identity is None:
            return default
        return reader(candidate.identity)

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def messageKind(self) -> str:  # noqa: N802
        return self._message_kind

    @Property(bool, notify=stateChanged)
    def hasSelection(self) -> bool:  # noqa: N802
        return self._candidate is not None and self._candidate.identity is not None

    @Property(bool, notify=stateChanged)
    def needsConfirmation(self) -> bool:  # noqa: N802
        return self._candidate is not None and self._candidate.needs_confirmation

    @Property(bool, notify=stateChanged)
    def canInstall(self) -> bool:  # noqa: N802
        return self._candidate is not None and self._candidate.is_usable

    @Property(str, notify=stateChanged)
    def selectedName(self) -> str:  # noqa: N802
        return self._selected_field(lambda identity: identity.display_name)

    @Property(str, notify=stateChanged)
    def selectedVersion(self) -> str:  # noqa: N802
        return self._selected_field(lambda identity: identity.version)

    @Property(str, notify=stateChanged)
    def selectedChecksum(self) -> str:  # noqa: N802
        return self._selected_field(lambda identity: identity.manifest_checksum)

    @Property(str, notify=stateChanged)
    def selectedFeatureCount(self) -> str:  # noqa: N802
        return self._selected_field(lambda identity: str(len(identity.contract.features)))

    @Property(str, notify=stateChanged)
    def selectedThreshold(self) -> str:  # noqa: N802
        return self._selected_field(
            lambda identity: f"{identity.contract.release_threshold:.3f}"
        )

    @Property(str, notify=stateChanged)
    def selectedArtifactCount(self) -> str:  # noqa: N802
        return self._selected_field(lambda identity: str(len(identity.artifacts)))

    @Property(str, notify=stateChanged)
    def selectedTrust(self) -> str:  # noqa: N802
        candidate = self._candidate
        return candidate.trust.value if candidate else ""

    @Property(str, notify=stateChanged)
    def selectedPath(self) -> str:  # noqa: N802
        candidate = self._candidate
        return str(candidate.manifest_path.parent) if candidate else "—"

    @Property(bool, notify=installedChanged)
    def hasInstalled(self) -> bool:  # noqa: N802
        return self._installed is not None

    @Property(str, notify=installedChanged)
    def installedName(self) -> str:  # noqa: N802
        installed = self._installed
        if installed is None or installed.identity is None:
            return "None"
        return f"{installed.identity.display_name} {installed.identity.version}"

    @Property(str, notify=installedChanged)
    def installedPath(self) -> str:  # noqa: N802
        installed = self._installed
        return str(installed.manifest_path.parent) if installed else "—"

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

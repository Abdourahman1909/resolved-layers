from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from variant_inference.infrastructure.model_package import (
    JsonModelPackageRepository,
    ModelPackageValidationError,
)
from variant_inference.qt.controller import SourceReviewController
from variant_inference.qt.table_model import CsvTableModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolved Layers by Computational Health Lab")
    parser.add_argument("--open", dest="source_path", type=Path, help="Open a CSV on startup")
    parser.add_argument(
        "--model-package",
        type=Path,
        default=None,
        help="Path to a validated Model Package manifest (never a loose pickle)",
    )
    parser.add_argument("--smoke", action="store_true", help="Load the QML shell, then exit")
    parser.add_argument("--screenshot", type=Path, help="Save one startup screenshot, then exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    application = QGuiApplication(sys.argv[:1])
    application.setApplicationName("Resolved Layers")
    application.setOrganizationName("Computational Health Lab")

    package_path = args.model_package
    if package_path is None and os.environ.get("CHL_MODEL_PACKAGE_MANIFEST"):
        package_path = Path(os.environ["CHL_MODEL_PACKAGE_MANIFEST"])
    package = None
    package_error = ""
    if package_path:
        try:
            package = JsonModelPackageRepository().load(package_path)
        except ModelPackageValidationError as error:
            package_error = str(error)

    project_root = Path(__file__).resolve().parents[2]
    identity_reference = project_root / ".impeccable" / "mocks" / "app" / "source-review-split-hybrid-v2.png"
    if not identity_reference.is_file():
        identity_reference = None

    table_model = CsvTableModel()
    controller = SourceReviewController(
        table_model,
        package,
        package_error=package_error,
        identity_reference=identity_reference,
    )
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("sourceController", controller)
    engine.rootContext().setContextProperty("sourceTableModel", table_model)
    qml_file = Path(__file__).with_name("qml") / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        return 2
    application.aboutToQuit.connect(controller.close)

    def clean_quit() -> None:
        roots = engine.rootObjects()
        if roots:
            roots[0].deleteLater()
        QTimer.singleShot(50, application.quit)

    if args.source_path:
        QTimer.singleShot(0, lambda: controller.openSource(str(args.source_path.resolve())))
    if args.screenshot:
        destination = args.screenshot.resolve()

        def capture() -> None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            window = engine.rootObjects()[0]
            application.primaryScreen().grabWindow(window.winId()).save(str(destination))
            clean_quit()

        QTimer.singleShot(1200, capture)
    elif args.smoke:
        QTimer.singleShot(750, clean_quit)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

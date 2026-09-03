from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from variant_inference import assets
from variant_inference.application.verified_run import VerifiedRunService
from variant_inference.application.variant_inspector import SourceRowEvidenceService
from variant_inference.application.evaluation import GroundTruthEvaluationService
from variant_inference.infrastructure.csv_source import CsvSourceReader
from variant_inference.infrastructure.model_package import (
    JsonModelPackageRepository,
    ModelPackageValidationError,
)
from variant_inference.infrastructure.production_inference import PickleEnsembleInference
from variant_inference.infrastructure.run_archive import DirectoryRunArchive
from variant_inference.qt.controller import SourceReviewController
from variant_inference.qt.profile_model import GroupBreakdownModel
from variant_inference.qt.results_controller import ResultsController
from variant_inference.qt.evaluation_controller import EvaluationController
from variant_inference.qt.evaluation_models import EvaluationCohortModel, EvaluationMetricModel
from variant_inference.qt.results_models import (
    InvestigationSetModel,
    PredictionTableModel,
    RunArchiveListModel,
    ScoreHistogramModel,
    SourceFieldListModel,
)
from variant_inference.qt.table_model import CsvTableModel


DESKTOP_FILE_NAME = "org.computationalhealthlab.ResolvedLayers"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolved Layers by Computational Health Lab")
    parser.add_argument("--open", dest="source_path", type=Path, help="Open a CSV on startup")
    parser.add_argument(
        "--model-package",
        type=Path,
        default=None,
        help="Path to a validated Model Package manifest (never a loose pickle)",
    )
    parser.add_argument(
        "--trusted-manifest-sha256",
        action="append",
        default=[],
        help="Trusted Model Package manifest SHA-256; may be supplied more than once",
    )
    parser.add_argument(
        "--run-archive",
        type=Path,
        default=None,
        help="Local directory for immutable Verified Runs",
    )
    parser.add_argument(
        "--open-run",
        help="Open one immutable Verified Run from the configured archive",
    )
    parser.add_argument(
        "--inspect-source-row",
        type=int,
        help="Open Records and select one Source Row for verification",
    )
    parser.add_argument("--smoke", action="store_true", help="Load the QML shell, then exit")
    parser.add_argument("--screenshot", type=Path, help="Save one startup screenshot, then exit")
    parser.add_argument(
        "--window-size",
        help="Set the verification window size as WIDTHxHEIGHT",
    )
    parser.add_argument(
        "--surface",
        choices=("review", "profile", "results", "evaluation"),
        default="review",
        help="Initial surface used by automated visual verification",
    )
    parser.add_argument(
        "--evaluation-label-column",
        help="Explicit label column for Evaluation verification",
    )
    parser.add_argument(
        "--evaluation-pathogenic-value",
        help="Exact raw value mapped to Pathogenic for Evaluation verification",
    )
    parser.add_argument(
        "--evaluation-benign-value",
        help="Exact raw value mapped to Benign for Evaluation verification",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    application = QGuiApplication(sys.argv[:1])
    application.setApplicationName("Resolved Layers")
    application.setOrganizationName("Computational Health Lab")
    application.setDesktopFileName(DESKTOP_FILE_NAME)

    window_icon = QIcon()
    for icon_path in assets.window_icon_paths():
        window_icon.addFile(str(icon_path))
    if not window_icon.isNull():
        application.setWindowIcon(window_icon)

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

    trusted_checksums = {
        value.strip().lower()
        for value in args.trusted_manifest_sha256
        if value.strip()
    }
    trusted_checksums.update(
        value.strip().lower()
        for value in os.environ.get("CHL_TRUSTED_MODEL_PACKAGE_SHA256", "").split(",")
        if value.strip()
    )
    run_archive_path = args.run_archive
    if run_archive_path is None and os.environ.get("CHL_RUN_ARCHIVE"):
        run_archive_path = Path(os.environ["CHL_RUN_ARCHIVE"])
    if run_archive_path is None:
        run_archive_path = Path(
            QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        ) / "runs"

    archive = DirectoryRunArchive(run_archive_path)
    verified_runs = None
    run_unavailable_reason = ""
    if package is None:
        # A build ships without a Model Package. Source Review, Dataset Profile,
        # and archived Verified Runs stay fully usable; prediction states plainly
        # that no package is installed rather than implying a transient fault.
        run_unavailable_reason = (
            package_error if package_error else "No Model Package installed"
        )
    elif package.manifest_checksum.lower() not in trusted_checksums:
        run_unavailable_reason = "Trust this Model Package checksum before prediction"
    else:
        verified_runs = VerifiedRunService(
            PickleEnsembleInference(trusted_checksums),
            archive,
        )

    identity_lockup = assets.LOCKUP if assets.LOCKUP.is_file() else None

    table_model = CsvTableModel()
    group_model = GroupBreakdownModel()
    prediction_model = PredictionTableModel()
    histogram_model = ScoreHistogramModel()
    investigation_set_model = InvestigationSetModel()
    archive_model = RunArchiveListModel()
    source_field_model = SourceFieldListModel()
    evaluation_metric_model = EvaluationMetricModel()
    evaluation_cohort_model = EvaluationCohortModel()
    evaluation_controller = EvaluationController(
        GroundTruthEvaluationService(archive, CsvSourceReader()),
        evaluation_metric_model,
        evaluation_cohort_model,
    )
    results_controller = ResultsController(
        archive,
        prediction_model,
        histogram_model,
        investigation_set_model,
        archive_model,
        SourceRowEvidenceService(archive, CsvSourceReader()),
        source_field_model,
    )
    controller = SourceReviewController(
        table_model,
        group_model,
        package,
        package_error=package_error,
        identity_lockup=identity_lockup,
        verified_runs=verified_runs,
        run_unavailable_reason=run_unavailable_reason,
        results_controller=results_controller,
        evaluation_controller=evaluation_controller,
    )
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("sourceController", controller)
    engine.rootContext().setContextProperty("sourceTableModel", table_model)
    engine.rootContext().setContextProperty("groupBreakdownModel", group_model)
    engine.rootContext().setContextProperty("resultsController", results_controller)
    engine.rootContext().setContextProperty("predictionTableModel", prediction_model)
    engine.rootContext().setContextProperty("scoreHistogramModel", histogram_model)
    engine.rootContext().setContextProperty("investigationSetModel", investigation_set_model)
    engine.rootContext().setContextProperty("runArchiveModel", archive_model)
    engine.rootContext().setContextProperty("sourceFieldModel", source_field_model)
    engine.rootContext().setContextProperty("evaluationController", evaluation_controller)
    engine.rootContext().setContextProperty("evaluationMetricModel", evaluation_metric_model)
    engine.rootContext().setContextProperty("evaluationCohortModel", evaluation_cohort_model)
    qml_file = Path(__file__).with_name("qml") / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        return 2
    if args.window_size:
        try:
            width, height = (int(value) for value in args.window_size.lower().split("x", 1))
            if width < 1 or height < 1:
                raise ValueError
        except ValueError:
            return 2
        window = engine.rootObjects()[0]
        window.setProperty("width", width)
        window.setProperty("height", height)
    application.aboutToQuit.connect(controller.close)

    def clean_quit() -> None:
        roots = engine.rootObjects()
        if roots:
            roots[0].deleteLater()
        QTimer.singleShot(50, application.quit)

    if args.source_path:
        QTimer.singleShot(0, lambda: controller.openSource(str(args.source_path.resolve())))
        if args.surface == "profile":
            QTimer.singleShot(100, lambda: controller.setActiveSurface("profile"))
    if args.open_run:
        def authorize_visual_evaluation() -> None:
            if not (
                args.evaluation_label_column
                and args.evaluation_pathogenic_value
                and args.evaluation_benign_value
            ):
                return
            if evaluation_controller.busy:
                QTimer.singleShot(25, authorize_visual_evaluation)
                return
            if not evaluation_controller.sourceAvailable:
                return
            if evaluation_controller.selectedLabelColumn != args.evaluation_label_column:
                evaluation_controller.selectLabelColumn(args.evaluation_label_column)
                QTimer.singleShot(25, authorize_visual_evaluation)
                return
            if not evaluation_controller.labelValues:
                QTimer.singleShot(25, authorize_visual_evaluation)
                return
            if not evaluation_controller.hasCoveragePreview:
                evaluation_controller.reviewCoverage(
                    args.evaluation_pathogenic_value,
                    args.evaluation_benign_value,
                )
                QTimer.singleShot(25, authorize_visual_evaluation)
                return
            if not evaluation_controller.hasReport:
                evaluation_controller.authorizeEvaluation(
                    args.evaluation_pathogenic_value,
                    args.evaluation_benign_value,
                )

        def open_run() -> None:
            if controller.openArchivedRun(args.open_run) and args.surface == "evaluation":
                controller.setActiveSurface("evaluation")
                if (
                    args.evaluation_label_column
                    and args.evaluation_pathogenic_value
                    and args.evaluation_benign_value
                ):
                    QTimer.singleShot(25, authorize_visual_evaluation)

        QTimer.singleShot(0, open_run)
    if args.inspect_source_row:
        def open_inspector() -> None:
            results_controller.showRecords()
            results_controller.selectRecordAt(args.inspect_source_row - 1)

        QTimer.singleShot(180, open_inspector)
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

"""Derive a sibling Model Package that differs only in its Release Threshold.

The Release Threshold is a classification boundary, not a model parameter. Two
packages built from the same weights produce the same probabilities and disagree
only about where Benign becomes Pathogenic. Deriving the second package rather
than assembling it by hand is what makes that guarantee checkable: the artifacts
are copied byte for byte and re-verified against the checksums the source
manifest already declares.

Changing the threshold changes the Inference Contract, so its canonical checksum
is recomputed here with the same rule `JsonModelPackageRepository` validates
against, and the manifest SHA-256 changes with it. The new manifest checksum is
printed for pinning in `OFFICIAL_MANIFEST_CHECKSUMS`; a package this release does
not recognise cannot be installed without the operator confirming it by hand.

The manifest's `benchmark_reference` records a confusion matrix, which the new
threshold makes false. It is re-derived by running real inference against the
benchmark source the source manifest names, so the file cannot be produced
without the benchmark it claims. The recorded `predictions_sha256` carries
through unchanged and correctly: it references a four-decimal comparison of
probabilities, and probabilities do not move.

Everything this touches lives outside the repository. Paths are arguments with
no defaults, and nothing restricted is written into the checkout.

    .venv/bin/python scripts/derive_threshold_package.py \
        --source-package  /path/to/teknofest-2026-pdr-v1 \
        --output-package  /path/to/teknofest-2026-pdr-v1-threshold-075 \
        --threshold       0.75 \
        --benchmark-source /path/to/training_lab_heldout_test_set.csv \
        --benchmark-label-column label
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from variant_inference.infrastructure.csv_source import CsvSourceReader  # noqa: E402
from variant_inference.infrastructure.model_package import (  # noqa: E402
    JsonModelPackageRepository,
    ModelPackageValidationError,
)
from variant_inference.infrastructure.production_inference import (  # noqa: E402
    PickleEnsembleInference,
)

MANIFEST_FILENAME = "manifest.json"


def canonical_checksum(payload: Mapping[str, Any]) -> str:
    """The Inference Contract checksum rule, matching the repository exactly."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_source_manifest(package_root: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = package_root / MANIFEST_FILENAME if package_root.is_dir() else package_root
    if not manifest_path.is_file():
        raise SystemExit(f"No {MANIFEST_FILENAME} at {package_root}")
    return manifest_path, json.loads(manifest_path.read_text(encoding="utf-8"))


def _copy_artifacts(source_root: Path, output_root: Path, artifacts: list[dict[str, Any]]) -> None:
    """Copy each declared artifact and prove the copy still matches its checksum.

    A silent copy failure would produce a package that validates against its own
    recomputed digests while no longer holding the released weights, so the
    declared checksum is the one checked, never a freshly computed one.
    """
    for artifact in artifacts:
        relative = Path(str(artifact["path"]))
        origin = source_root / relative
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, destination)
        copied = file_checksum(destination)
        if copied != str(artifact["sha256"]).lower():
            raise SystemExit(
                f"Copied artifact does not match its declared checksum: {relative}"
            )


def _confusion_at_threshold(
    manifest_path: Path,
    benchmark_source: Path,
    label_column: str,
    pathogenic_label: str,
) -> dict[str, int]:
    """Run the real ensemble once and count the new classification outcome."""
    package = JsonModelPackageRepository().load(manifest_path)
    source = CsvSourceReader().open(benchmark_source)
    try:
        predictions = PickleEnsembleInference({package.manifest_checksum.lower()}).predict(
            source, package
        )
        labels = _read_labels(benchmark_source, label_column)
    finally:
        source.close()

    if len(labels) != len(predictions):
        raise SystemExit(
            f"Benchmark has {len(labels)} labels for {len(predictions)} predictions."
        )

    counts = {"tn": 0, "fp": 0, "fn": 0, "tp": 0}
    for record, label in zip(predictions, labels):
        actual = label == pathogenic_label
        predicted = record.prediction == "Pathogenic"
        if actual and predicted:
            counts["tp"] += 1
        elif actual:
            counts["fn"] += 1
        elif predicted:
            counts["fp"] += 1
        else:
            counts["tn"] += 1
    return counts


def _read_labels(path: Path, column: str) -> list[str]:
    import csv

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise SystemExit(f"Benchmark source has no '{column}' column.")
        return [(row.get(column) or "").strip() for row in reader]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source-package", type=Path, required=True)
    parser.add_argument("--output-package", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--benchmark-source", type=Path, required=True)
    parser.add_argument("--benchmark-label-column", default="label")
    parser.add_argument("--benchmark-pathogenic-label", default="1")
    parser.add_argument(
        "--package-id-suffix",
        default="",
        help="Appended to package_id and version so the two are distinguishable",
    )
    parser.add_argument(
        "--display-name-suffix",
        default="",
        help="Appended to display_name, which is what Settings shows",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    source_manifest_path, manifest = _read_source_manifest(args.source_package.expanduser())
    source_root = source_manifest_path.parent

    # Validating the source before deriving from it means a package that has
    # already drifted cannot silently become the parent of a second one.
    try:
        JsonModelPackageRepository().load(source_manifest_path)
    except ModelPackageValidationError as error:
        raise SystemExit(f"Source Model Package rejected: {error}")

    benchmark = args.benchmark_source.expanduser().resolve()
    declared_source = str(manifest.get("benchmark_reference", {}).get("source_sha256", ""))
    actual_source = file_checksum(benchmark)
    if declared_source and declared_source != actual_source:
        raise SystemExit(
            "Benchmark source does not match the one the source manifest names.\n"
            f"  declared {declared_source}\n  supplied {actual_source}"
        )

    output_root = args.output_package.expanduser().resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"Output package already exists and is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    _copy_artifacts(source_root, output_root, manifest["artifacts"])

    contract = dict(manifest["inference_contract"])
    previous_threshold = float(contract["release_threshold"])
    contract["release_threshold"] = args.threshold
    if args.package_id_suffix:
        contract["contract_id"] = f"{contract['contract_id']}{args.package_id_suffix}"
        contract["version"] = f"{contract['version']}{args.package_id_suffix}"
    contract.pop("checksum", None)
    contract["checksum"] = canonical_checksum(contract)

    derived = dict(manifest)
    derived["inference_contract"] = contract
    if args.package_id_suffix:
        derived["package_id"] = f"{manifest['package_id']}{args.package_id_suffix}"
        derived["version"] = f"{manifest['version']}{args.package_id_suffix}"
    if args.display_name_suffix:
        derived["display_name"] = f"{manifest['display_name']}{args.display_name_suffix}"

    # Written once with a placeholder matrix so the contract can be loaded, then
    # rewritten with the real one. Only the final file's checksum is reported.
    output_manifest = output_root / MANIFEST_FILENAME
    output_manifest.write_text(
        json.dumps(derived, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    confusion = _confusion_at_threshold(
        output_manifest,
        benchmark,
        args.benchmark_label_column,
        args.benchmark_pathogenic_label,
    )
    benchmark_reference = dict(derived.get("benchmark_reference", {}))
    benchmark_reference["expected_confusion_matrix"] = confusion
    derived["benchmark_reference"] = benchmark_reference
    output_manifest.write_text(
        json.dumps(derived, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Load the finished package the way the application will, so the file that
    # gets pinned is one that has actually passed validation.
    identity = JsonModelPackageRepository().load(output_manifest)

    print(f"source package     {source_root}")
    print(f"derived package    {output_root}")
    print(f"threshold          {previous_threshold} -> {identity.contract.release_threshold}")
    print(f"package_id         {identity.package_id}")
    print(f"display_name       {identity.display_name}")
    print(f"version            {identity.version}")
    print(f"artifacts          {len(identity.artifacts)} verified")
    print(f"features           {len(identity.contract.features)}")
    print(f"contract checksum  {identity.contract.checksum}")
    print(f"manifest sha256    {identity.manifest_checksum}")
    print(
        "benchmark          "
        f"tn {confusion['tn']} fp {confusion['fp']} "
        f"fn {confusion['fn']} tp {confusion['tp']}"
    )
    print()
    print("Pin the manifest sha256 in OFFICIAL_MANIFEST_CHECKSUMS to install it without a prompt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

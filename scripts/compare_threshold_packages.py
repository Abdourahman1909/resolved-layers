"""Prove two Model Packages differ only in where they draw the boundary.

Two packages built from the same weights should produce the same probabilities
and disagree only about classification. The inference core makes that true by
construction — the threshold reaches one comparison, after every score is
computed — but the second package is a separate copy of the artifacts, and a
copy error would be invisible to that argument. This runs both packages over the
same source and checks the claim against real output.

The check is exact. Ensemble, component, and disagreement values must match to
the full twelve decimal places the records carry, not to a tolerance. Every row
whose classification differs must have a score inside the interval between the
two thresholds, and every row inside that interval must differ; a single
exception in either direction fails.

    .venv/bin/python scripts/compare_threshold_packages.py \
        --package /path/to/teknofest-2026-pdr-v1 \
        --package /path/to/teknofest-2026-pdr-v1-threshold-075 \
        --source  /path/to/training_lab_heldout_test_set.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def _run(package_path: Path, source_path: Path):
    manifest = package_path / MANIFEST_FILENAME if package_path.is_dir() else package_path
    try:
        package = JsonModelPackageRepository().load(manifest)
    except ModelPackageValidationError as error:
        raise SystemExit(f"Model Package rejected: {manifest}\n  {error}")
    source = CsvSourceReader().open(source_path)
    try:
        records = PickleEnsembleInference({package.manifest_checksum.lower()}).predict(
            source, package
        )
    finally:
        source.close()
    return package, records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--package", type=Path, action="append", required=True)
    parser.add_argument("--source", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if len(args.package) != 2:
        raise SystemExit("Pass --package exactly twice.")

    source_path = args.source.expanduser().resolve()
    left_package, left = _run(args.package[0].expanduser().resolve(), source_path)
    right_package, right = _run(args.package[1].expanduser().resolve(), source_path)

    low = min(left_package.contract.release_threshold, right_package.contract.release_threshold)
    high = max(left_package.contract.release_threshold, right_package.contract.release_threshold)

    print(f"source             {source_path.name}")
    print(f"package A          {left_package.display_name} {left_package.version}")
    print(f"                   threshold {left_package.contract.release_threshold}")
    print(f"package B          {right_package.display_name} {right_package.version}")
    print(f"                   threshold {right_package.contract.release_threshold}")
    print(f"records            {len(left)} / {len(right)}")

    failures: list[str] = []
    if len(left) != len(right):
        failures.append(f"record counts differ: {len(left)} and {len(right)}")

    reclassified = 0
    for a, b in zip(left, right):
        if a.source_row != b.source_row:
            failures.append(f"Source Row order differs at {a.source_row} / {b.source_row}")
            break
        if a.ensemble_score != b.ensemble_score:
            failures.append(
                f"row {a.source_row}: ensemble {a.ensemble_score!r} vs {b.ensemble_score!r}"
            )
        if a.component_scores != b.component_scores:
            failures.append(
                f"row {a.source_row}: components {a.component_scores!r} vs {b.component_scores!r}"
            )
        if a.model_disagreement != b.model_disagreement:
            failures.append(
                f"row {a.source_row}: disagreement "
                f"{a.model_disagreement!r} vs {b.model_disagreement!r}"
            )

        inside = low <= a.ensemble_score < high
        differs = a.prediction != b.prediction
        if differs:
            reclassified += 1
        if differs and not inside:
            failures.append(
                f"row {a.source_row}: classification differs at score "
                f"{a.ensemble_score} which is outside [{low}, {high})"
            )
        if inside and not differs:
            failures.append(
                f"row {a.source_row}: score {a.ensemble_score} lies in "
                f"[{low}, {high}) but both packages call it {a.prediction}"
            )

    def pathogenic(records) -> int:
        return sum(1 for record in records if record.prediction == "Pathogenic")

    print(f"A pathogenic       {pathogenic(left)}")
    print(f"B pathogenic       {pathogenic(right)}")
    print(f"reclassified       {reclassified} rows, all within [{low}, {high})")

    if failures:
        print()
        print(f"FAILED with {len(failures)} problem(s):")
        for problem in failures[:20]:
            print(f"  {problem}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
        return 1

    print()
    print(
        "Identical scores. Every ensemble, component, and disagreement value matches "
        "exactly;\nthe packages differ only in classification, and only where the score "
        "falls between\ntheir thresholds."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

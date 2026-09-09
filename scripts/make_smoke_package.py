"""Build a throwaway Model Package that a packaged build can actually run.

A bundled build loads CatBoost and LightGBM as native libraries that no static
import names, so a broken bundle starts normally and fails only when someone
asks it to predict. `--verify-inference` exists to catch that, but it needs a
Model Package, and no real one may be committed. On a machine where nobody can
click the interface — a continuous integration runner building the Windows
executable — that leaves the most important failure undetected.

This trains two tiny boosters on synthetic random data and assembles them into a
structurally real Model Package: correct artifact roles, correct checksums, a
contract with numeric and categorical features, and a small source CSV to run it
against. Nothing here comes from the organisers and the models predict nothing
meaningful. It exists only to prove that a build can unpickle boosters and
execute them.

    .venv/bin/python scripts/make_smoke_package.py --output build/smoke

Then, against any build:

    resolved-layers --verify-inference \
        --model-package build/smoke/package/manifest.json \
        --open build/smoke/source.csv
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import shutil
import sys
from pathlib import Path

SEED = 20260909
ROWS = 64
CATEGORIES = ("A", "B", "C", "Unknown")
PANELS = ("Panel-A", "Panel-B", "Unknown")


def canonical_checksum(payload: dict) -> str:
    """The Inference Contract checksum rule the repository validates against."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _training_frame():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(SEED)
    frame = pd.DataFrame(
        {
            "Feature_A": rng.normal(size=ROWS),
            "Feature_B": rng.normal(size=ROWS),
            "Category": rng.choice(CATEGORIES, size=ROWS),
            "Panel": rng.choice(PANELS, size=ROWS),
        }
    )
    # A learnable signal, so both boosters produce two-column probabilities
    # rather than collapsing to a single observed class.
    labels = ((frame["Feature_A"] + frame["Feature_B"]) > 0).astype(int)
    labels.iloc[:4] = 1 - labels.iloc[:4]  # a little noise
    return frame, labels


def _fit_models(frame, labels):
    from catboost import CatBoostClassifier
    from lightgbm import LGBMClassifier
    import pandas as pd

    categorical = ["Category", "Panel"]

    catboost_frame = frame.copy()
    for column in categorical:
        catboost_frame[column] = catboost_frame[column].astype(str)
    catboost = CatBoostClassifier(
        iterations=20, depth=2, verbose=0, random_seed=SEED, allow_writing_files=False
    )
    catboost.fit(catboost_frame, labels, cat_features=categorical)

    lightgbm_frame = frame.copy()
    lightgbm_frame["Category"] = pd.Categorical(
        lightgbm_frame["Category"].astype(str), categories=list(CATEGORIES)
    )
    lightgbm_frame["Panel"] = pd.Categorical(
        lightgbm_frame["Panel"].astype(str), categories=list(PANELS)
    )
    lightgbm = LGBMClassifier(n_estimators=20, num_leaves=4, verbose=-1, random_state=SEED)
    lightgbm.fit(lightgbm_frame, labels)

    return catboost, lightgbm


def _contract() -> dict:
    contract = {
        "contract_id": "chl.smoke.packaged-build.contract",
        "version": "0.smoke",
        "features": [
            {"name": "Feature_A", "presence": "required", "kind": "numeric"},
            {"name": "Feature_B", "presence": "required", "kind": "numeric"},
            {
                "name": "Category",
                "presence": "required",
                "kind": "categorical",
                "allowed_categories": list(CATEGORIES),
                "unknown_category": "Unknown",
                "missing_representation": "Unknown",
            },
            {
                "name": "Panel",
                "presence": "omissible",
                "kind": "categorical",
                "allowed_categories": list(PANELS),
                "unknown_category": "Unknown",
                "missing_representation": "Unknown",
            },
        ],
        "ensemble_weights": {"catboost": 0.5, "lightgbm": 0.5},
        "release_threshold": 0.5,
        "row_filtering": "none",
        "component_input_policy": {
            "catboost": {
                "categorical_missing": "Unknown",
                "categorical_unseen": "preserve_as_string",
            },
            "lightgbm": {
                "categorical_missing": "missing",
                "categorical_unseen": "missing",
                "category_order": "allowed_categories",
            },
        },
    }
    contract["checksum"] = canonical_checksum(contract)
    return contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    root = Path(args.output).expanduser().resolve()
    package = root / "package"
    if root.exists():
        shutil.rmtree(root)
    package.mkdir(parents=True)

    frame, labels = _training_frame()
    catboost, lightgbm = _fit_models(frame, labels)

    artifacts = []
    for role, name, model in (
        ("catboost_model", "catboost_smoke.pkl", catboost),
        ("lightgbm_model", "lightgbm_smoke.pkl", lightgbm),
    ):
        path = package / name
        path.write_bytes(pickle.dumps(model))
        artifacts.append(
            {
                "role": role,
                "path": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )

    manifest = {
        "schema_version": 1,
        "package_id": "chl.smoke.packaged-build",
        "display_name": "Packaged build smoke package",
        "version": "0.smoke",
        "distribution": "development-only",
        "development_only": True,
        "artifacts": artifacts,
        "inference_contract": _contract(),
    }
    manifest_path = package / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # A source carrying the contract's features plus a Context Column, so the
    # run exercises column selection rather than a bare feature matrix.
    source = root / "source.csv"
    lines = ["Record_ID,Feature_A,Feature_B,Category,Panel,note"]
    for index in range(8):
        lines.append(
            f"SMOKE-{index + 1:03d},{index - 4}.5,{4 - index}.25,"
            f"{CATEGORIES[index % len(CATEGORIES)]},"
            f"{PANELS[index % len(PANELS)]},row {index + 1}"
        )
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")

    checksum = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(f"package    {package}")
    print(f"source     {source}")
    print(f"manifest   {checksum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

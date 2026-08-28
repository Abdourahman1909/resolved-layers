from __future__ import annotations

import os
import subprocess
import sys


def test_dataset_profile_qml_starts_without_runtime_errors(fixture_dir):
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "variant_inference",
            "--model-package",
            str(fixture_dir / "development-package" / "manifest.json"),
            "--open",
            str(fixture_dir / "dataset_profile.csv"),
            "--surface",
            "profile",
            "--smoke",
        ),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr

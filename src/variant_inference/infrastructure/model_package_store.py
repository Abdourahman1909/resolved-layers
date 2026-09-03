"""Persist the operator's Model Package choices for this machine.

The store holds a path and a set of confirmed checksums. It holds no model
artifacts, no weights, and no organizer data, so it is safe to keep in an
ordinary user configuration directory.

Every read fails soft. A missing, unreadable, or malformed configuration yields
empty settings rather than an error, because a damaged file must never stop the
application from starting; the operator simply chooses a package again.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from variant_inference.domain.models import ModelPackageSettings

SCHEMA_VERSION = 1


class JsonModelPackageSettingsStore:
    """A single JSON file holding the installed package and confirmed checksums."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ModelPackageSettings:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return ModelPackageSettings()
        if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
            return ModelPackageSettings()

        raw_path = payload.get("manifest_path")
        manifest_path = Path(raw_path) if isinstance(raw_path, str) and raw_path else None

        raw_checksums = payload.get("confirmed_checksums", [])
        confirmed = frozenset(
            value.strip().lower()
            for value in raw_checksums
            if isinstance(value, str) and value.strip()
        ) if isinstance(raw_checksums, list) else frozenset()

        return ModelPackageSettings(manifest_path=manifest_path, confirmed_checksums=confirmed)

    def save(self, settings: ModelPackageSettings) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "manifest_path": str(settings.manifest_path) if settings.manifest_path else None,
            "confirmed_checksums": sorted(settings.confirmed_checksums),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._write_atomically(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_atomically(self, text: str) -> None:
        """Replace the file in one step so an interrupted save cannot truncate it."""
        handle, temporary = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=self._path.name, suffix=".tmp"
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

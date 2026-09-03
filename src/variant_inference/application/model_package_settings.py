"""Let an operator install a Model Package without a terminal.

A distributed build ships no Model Package. The operator receives one
separately and points the application at it once. This service validates that
choice, decides whether it may be deserialized, and remembers the decision.

Trust is the point of this module. Model artifacts are unpickled, and
unpickling executes code, so structural validity is never sufficient. A package
runs only when its exact manifest checksum is either pinned in this release as
official, or was explicitly confirmed by the operator beforehand.
"""

from __future__ import annotations

from pathlib import Path

from variant_inference.application.ports import (
    ModelPackageRepository,
    ModelPackageSettingsStore,
)
from variant_inference.domain.models import (
    ModelPackageCandidate,
    ModelPackageSettings,
    ModelPackageTrust,
)

# Manifest SHA-256 of packages this release recognises without asking. A
# checksum identifies a package; it discloses nothing about the weights,
# features, or organizer data inside it.
OFFICIAL_MANIFEST_CHECKSUMS: frozenset[str] = frozenset(
    {
        # TEKNOFEST 2026 Missense CatBoost-LightGBM PDR Release 1.0.0-pdr
        "fc20e611197bbe65f9d5cda058c7367bf32d54df95dd77f5af3d3c59fb8d923d",
    }
)

MANIFEST_FILENAME = "manifest.json"


class ModelPackageInstallationService:
    """Inspect, confirm, and remember the operator's Model Package choice."""

    def __init__(
        self,
        packages: ModelPackageRepository,
        store: ModelPackageSettingsStore,
        official_checksums: frozenset[str] = OFFICIAL_MANIFEST_CHECKSUMS,
    ) -> None:
        self._packages = packages
        self._store = store
        self._official = frozenset(value.strip().lower() for value in official_checksums)

    # Inspection -----------------------------------------------------------

    def inspect(self, selected: Path) -> ModelPackageCandidate:
        """Validate a chosen manifest or package folder without loading models.

        Accepts either the manifest itself or the folder containing it, because
        an operator picking a package naturally selects the folder.
        """
        manifest_path = self._resolve_manifest(selected)
        if manifest_path is None:
            return ModelPackageCandidate(
                manifest_path=Path(selected),
                trust=ModelPackageTrust.INVALID,
                problem=f"No {MANIFEST_FILENAME} found in the selected location.",
            )

        try:
            identity = self._packages.load(manifest_path)
        except Exception as error:  # the repository raises its own validation error
            return ModelPackageCandidate(
                manifest_path=manifest_path,
                trust=ModelPackageTrust.INVALID,
                problem=str(error),
            )

        return ModelPackageCandidate(
            manifest_path=manifest_path,
            trust=self._trust_for(identity.manifest_checksum),
            identity=identity,
        )

    def _resolve_manifest(self, selected: Path) -> Path | None:
        path = Path(selected).expanduser()
        if path.is_file():
            return path.resolve()
        candidate = path / MANIFEST_FILENAME
        if candidate.is_file():
            return candidate.resolve()
        return None

    def _trust_for(self, checksum: str) -> ModelPackageTrust:
        normalised = checksum.strip().lower()
        if normalised in self._official:
            return ModelPackageTrust.OFFICIAL
        if normalised in self.settings().confirmed_checksums:
            return ModelPackageTrust.CONFIRMED
        return ModelPackageTrust.UNCONFIRMED

    # Operator decisions ---------------------------------------------------

    def confirm(self, candidate: ModelPackageCandidate) -> ModelPackageCandidate:
        """Record that the operator vouched for this exact manifest checksum."""
        if candidate.identity is None:
            raise ValueError("An invalid Model Package cannot be confirmed.")
        settings = self.settings().with_confirmed(candidate.manifest_checksum)
        self._store.save(settings)
        return ModelPackageCandidate(
            manifest_path=candidate.manifest_path,
            trust=self._trust_for(candidate.manifest_checksum),
            identity=candidate.identity,
        )

    def install(self, candidate: ModelPackageCandidate) -> ModelPackageCandidate:
        """Make a trusted candidate the package this machine loads at startup."""
        if not candidate.is_usable:
            raise ValueError("Confirm this Model Package before installing it.")
        settings = self.settings().with_manifest(candidate.manifest_path)
        self._store.save(settings)
        return candidate

    def remove(self) -> None:
        """Stop loading a Model Package at startup, keeping past confirmations."""
        self._store.save(self.settings().with_manifest(None))

    # Startup --------------------------------------------------------------

    def settings(self) -> ModelPackageSettings:
        return self._store.load()

    def configured(self) -> ModelPackageCandidate | None:
        """Return the installed package, revalidated, or None when unset.

        Revalidation matters: the package folder may have moved, been edited, or
        had an artifact replaced since it was installed.
        """
        manifest_path = self.settings().manifest_path
        if manifest_path is None:
            return None
        return self.inspect(manifest_path)

    def trusted_checksums(self) -> set[str]:
        """Every checksum this machine may deserialize."""
        return set(self._official | self.settings().confirmed_checksums)

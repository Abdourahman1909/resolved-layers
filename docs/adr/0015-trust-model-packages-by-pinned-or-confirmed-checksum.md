---
status: accepted
---

# Trust a Model Package only by pinned or operator-confirmed manifest checksum

A distributed build ships no Model Package, so an operator must be able to install one from the interface rather than from a terminal. Loading a package deserializes model artifacts, and deserialization executes code, so structural validity can never be sufficient on its own.

A Model Package is loaded only when its exact manifest SHA-256 is either pinned in the release as an official Computational Health Lab package, or was explicitly confirmed by the operator beforehand. Selecting a package validates its manifest, verifies every declared artifact checksum, and presents package identity, feature count, Release Threshold, artifact count, checksum, and location as evidence. An unrecognized package is shown with an explicit trust warning and cannot be installed until the operator confirms that exact checksum. Confirmations are recorded per checksum, so confirming one package never trusts another, and a package whose artifacts change after installation stops being usable rather than loading silently.

The stored configuration holds only a path and confirmed checksums. No model artifact, weight, mapping, or organizer data is copied into it, so it remains safe in an ordinary user configuration directory. A missing, unreadable, or future-schema configuration reads as empty settings so a damaged file cannot prevent startup.

This costs the operator one deliberate confirmation for any package the release does not already recognize, and it means a rebuilt package must be confirmed again because its checksum changes. The trade-off is deliberate: an interface convenient enough to be used by someone who is not the developer must not become a path for executing an unverified pickle, and the operator remains the explicit trust authority rather than the file picker.

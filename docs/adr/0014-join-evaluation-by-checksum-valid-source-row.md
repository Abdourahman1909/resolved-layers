---
status: accepted
---

# Join Evaluation only through a checksum-valid Source Row boundary

Observed Evaluation reads authorized raw labels only from the original Source Dataset while its SHA-256 checksum and dimensions still match the immutable Verified Run, then joins each label to exactly one ordered prediction through the one-based Source Row. Evaluation never copies labels into or mutates the Verified Run, never lets QML parse source data or calculate metrics, and never silently treats missing or unrecognized labels as evaluated rows.

This boundary costs repeated source verification and makes Evaluation unavailable when the external source is missing or modified. The trade-off is deliberate: confusion counts, denominators, metrics, and error cohorts remain traceable to exact source evidence without weakening Verified Run immutability or fabricating performance from ambiguous rows.

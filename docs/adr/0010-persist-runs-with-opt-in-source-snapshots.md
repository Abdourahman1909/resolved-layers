---
status: accepted
---

# Persist runs with opt-in Source Snapshots

Completed Prediction Runs persist locally with results and reproducibility evidence so investigations survive application restarts. The Run Archive does not silently duplicate potentially sensitive CSV data: a complete Source Snapshot is stored only after visible operator consent, while the default archive keeps the source path and checksum and detects later absence or modification.

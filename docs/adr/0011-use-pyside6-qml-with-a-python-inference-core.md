---
status: accepted
---

# Use PySide6/QML with a Python inference core

The first-release desktop client uses a custom PySide6/QML presentation layer over an in-process Python inference core. This keeps CatBoost, LightGBM, pandas, and the verified prediction pipeline in their native runtime and avoids a local web server or Python sidecar, while QML supports the required custom interface and virtualized tables; acceptance is conditional on avoiding generic Qt styling, validating packaged builds on every target OS, and resolving Qt/module licensing before public release.

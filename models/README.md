# Model Package artifacts

This directory is reserved for locally installed or release-managed Model Packages. The first release contains only the approved CatBoost–LightGBM package; later Research Mode releases may maintain multiple validated packages in a local Model Library.

Do not commit trained weights, organizer-derived mappings, or restricted data until publication permission and the release mechanism are confirmed. Every package must include integrity metadata and the complete Inference Contract required to reproduce predictions. Loose `.pkl` files and arbitrary model folders are not runnable packages.

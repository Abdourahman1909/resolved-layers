---
status: accepted
---

# Support a controlled Model Library

The application is structured around validated, integrity-checked Model Packages, with exactly one package fixed for each Prediction Run. The first release ships only the current CatBoost–LightGBM package and Competition Mode locks it, while a later Research Mode may select among installed Computational Health Lab packages; arbitrary model files remain unsupported because they cannot guarantee safe loading, compatible preprocessing, or reproducible meaning.

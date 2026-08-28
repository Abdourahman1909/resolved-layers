---
status: superseded by ADR-0009
---

# Bind the application to one Production Model

The application supports one versioned Production Model and its immutable Inference Contract instead of loading arbitrary model folders. This sacrifices experimentation inside the product in exchange for predictable input requirements, reproducible outputs, a simpler interface, and a defensible competition workflow; training and model comparison remain in the parent repository.

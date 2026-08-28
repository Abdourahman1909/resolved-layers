# ADR 0013: Name the product Resolved Layers

## Decision

Use **Resolved Layers** as the public product name and `resolved-layers` as the repository slug. Keep **Computational Health Lab** as the creator/owner identity and `Variant Inference` as the functional descriptor for the current missense-variant workflow.

## Rationale

Generic descriptive names were rejected because the application may later be public and support additional validated Computational Health Lab Model Packages. Resolved Layers is distinctive, already connected to the approved visual identity, and expresses complex evidence becoming ordered and inspectable without making a clinical claim.

## Consequences

Public-facing product surfaces use Resolved Layers. Technical Python modules may retain `variant_inference` where they describe the current domain, and the existing `variant-inference` command remains as a compatibility alias alongside `resolved-layers`.

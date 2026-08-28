# Product

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Stack

PySide6 with a custom QML/Qt Quick presentation layer and an in-process Python inference core. Linux and Windows receive tested first-release builds through `pyside6-deploy`/Nuitka; macOS is deferred unless a concrete lab need emerges.

## Users

- Computational Health Lab operators running and investigating variant predictions.
- TEKNOFEST judges verifying the selected source, deterministic execution, and output.
- Future research users working with compatible CSV datasets and validated lab Model Packages, subject to licensing and publication permission.

## Product Purpose

Provide a trustworthy desktop workspace for verifying a variant CSV, running a traceable Model Package, investigating cohort and individual predictions, evaluating authorized labels, and exporting reproducible results. TEKNOFEST is the first demanding deployment context, not the product's permanent boundary.

## Positioning

The product treats source evidence, preprocessing visibility, model identity, and run reproducibility as first-class parts of inference. It combines a competition-safe Verified Run with a separate Investigation Workspace instead of behaving like either a generic CSV uploader or a training dashboard.

## Operating Context

- Competition-critical inference remains local and functional without internet or AI services.
- Operators review and explicitly confirm Source Evidence before prediction.
- Completed runs persist locally and may be reopened for investigation.
- Competition Mode locks the official Model Package; a later Research Mode may use a controlled Model Library.

## Capabilities and Constraints

- One validated Model Package is fixed for each Prediction Run.
- All source columns remain inspectable, while only Model Features enter inference.
- The first release targets smooth operation through 10,000 variants on the competition laptop.
- Verified Runs, Analysis Sandbox state, Competition Export, and Research Export remain distinct.
- Label-dependent metrics require explicit Ground-Truth Authorization.
- AI and internet integration is deferred; the future assistant remains read-only.
- Linux and Windows are the first-release operating-system targets; macOS is deferred.
- The public license, accessibility target, and localization scope remain open.

## Brand Commitments

The product is named **Resolved Layers** and is created by Computational Health Lab. The Laboratory Identity remains the primary creator/owner identity across future competitions, models, applications, reports, and research. `Variant Inference` is the functional Product Descriptor for the current workflow, not the public product name.

The Laboratory Identity must not encode missense-variant prediction as the laboratory's permanent scope or rely on predictable DNA helices, medical crosses, heartbeat traces, or generic AI-brain imagery.

The accepted Laboratory Thesis is: **Computational Health Lab turns complex health data into transparent, testable computational evidence.** The identity should express complexity becoming clarity, with traceability and scientific rigor, without turning that thesis into a literal medical or algorithm icon.

The canonical Laboratory Display Name is **Computational Health Lab**, without hyphens. `CHL` is a secondary monogram for constrained spaces and does not replace the complete wordmark. The registered hyphenated competition-team form is used only where an official system requires it.

The final approved Laboratory Identity direction is **Resolved Layers**: the original full-color concept showing three open analytical planes overlapping around a shared evidence space, paired with the complete `Computational Health Lab` wordmark. The user explicitly locked the original shape, blue/black/gray color treatment, and overall appearance after reviewing both the initial alternatives and three monochrome refinements. The refinements are unselected explorations, not replacements. Production vector files must faithfully reconstruct the approved reference at compact application-icon size and in monochrome without reopening the concept decision. The earlier CHL monogram challenger remains rejected because it resembled a clothing-brand logo.

The primary visual environment is light-first because the identity and application must remain clear in laboratories, competition rooms, presentations, projectors, reports, and printed material. The logo must work in pure black and white. Dark mode is deferred until it can be designed as a complete secondary system rather than a color inversion.

The interface must be custom, beautiful, professional, calm, and immediately understandable. Generic upload theater, oversized KPI-card grids, decorative dashboard density, unmodified default toolkit styling, borrowed TEKNOFEST branding, and generic medical-blue dashboard styling are unacceptable.

## Evidence on Hand

- Product requirements: `docs/PRD.md`
- Canonical language: `CONTEXT.md`
- Architectural decisions: `docs/adr/`
- Durable project state: `docs/PROJECT_MEMORY.md`
- The parent training repository contains the current CatBoost–LightGBM artifacts, saved configuration, held-out evidence, and competition report; restricted datasets and model-derived mappings must not be copied into this repository without publication permission.

## Product Principles

1. Evidence before prediction.
2. One validated package per run.
3. Reproducibility by construction.
4. Professional restraint over dashboard density.
5. Local deterministic inference before optional intelligence.

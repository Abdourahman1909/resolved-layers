# Project Memory — Variant Inference App

> Durable context for future sessions working in this repository.
> Last consolidated: 2026-08-28.
> Read `AGENTS.md` first. Use `CONTEXT.md` for canonical terminology and `docs/adr/` for durable architectural decisions.

## 1. Product identity

- Working repository name: `variant-inference-app`; the public product name is not decided.
- Public naming requirement confirmed on August 28, 2026: the eventual open-source product must have a distinctive, ownable, non-generic name. Descriptive placeholders such as `variant-inference-app`, `CHL Resolve`, and generic `Evidence Studio`-style names are not acceptable as the public identity. GitHub remote creation is paused until a deliberate naming round and conflict scan produce a user-approved name.
- Owner identity: **Computational Health Lab**.
- Intended direction: a standalone, desktop-oriented application that may later be open sourced.
- TEKNOFEST is the first demanding deployment context, not the permanent product boundary. The product should remain useful for later compatible research CSVs, especially when they contain richer inspectable features or metadata.
- Parent training repository: the separate repository located one directory above this nested repository in the current development workspace. This relationship is local-development context, not a distributable runtime dependency.
- This is an independent nested Git repository. It must not become another interface layered into the parent Streamlit application.

## 2. Model and competition context

- Domain: binary missense-variant pathogenicity prediction: Pathogenic (`1`) or Benign (`0`).
- Competition: TEKNOFEST 2026 AI in Health, University and Above level.
- Team: Computational-Health-Lab; Team ID 763095; official finalist.
- Production Model: the current CatBoost and LightGBM ensemble reported for the final competition model.
- Reported ensemble weights are approximately CatBoost 0.5007 and LightGBM 0.4993.
- Reported decision threshold is 0.61.
- Reported genuine held-out F1 is 0.9067 on 736 rows.
- The model uses the organizer's anonymized feature space and requires its saved feature order, category mappings, missing-value behavior, weights, and threshold.
- Final test labels will be hidden. The jury may ask the team to rerun code and reproduce results.
- Public rules do not require an open-source repository, but readable source, deterministic inference, model/configuration artifacts, and a reproducible environment must be available for jury verification.

## 3. Confirmed product boundaries

- Each Prediction Run supports exactly one validated Model Package and its immutable Inference Contract.
- The architecture will support a local Model Library of Computational Health Lab packages, but it is not a generic model host and will never treat arbitrary `.pkl` files or model folders as runnable packages.
- The first core release ships only the current CatBoost–LightGBM Model Package. Competition Mode locks that official package. Model-package installation and Research Mode selection are deferred until the core single-package workflow is reliable.
- Primary workflow: select CSV, verify Source Evidence, validate the Inference Contract, run prediction, inspect focused results, and export outputs.
- Training, Optuna, ablation, unrestricted threshold changes, and experiment management remain in the parent training repository.
- The interface must not dedicate a mostly empty page to a large upload/drop target.
- The interface must not overwhelm users or judges with decorative metrics and excessive charts after prediction.
- The exact Source Dataset must remain visibly verifiable so a judge can connect what was selected to what was processed.
- Every column present in the Source Dataset should be inspectable, including available features or metadata that are not consumed by the Production Model. Their display and export relationship to predictions still needs to be resolved precisely.
- Accepted first-release record-view design, subject to usability revision after hands-on testing: keep a compact table containing identity, prediction, Ensemble Score, component agreement, and warnings available for targeted search, sorting, grouping, filtering, exact variant verification, and export; provide searchable column controls for every Model Feature and Context Column; show the complete selected row in the Variant Inspector. The table is an active record-analysis tool after the cohort is narrowed, not the primary way to investigate thousands of variants by manual browsing. Default view order remains Source Row order, and user sorting/grouping never changes official export order.
- Export boundary: Competition Export remains minimal, while Research Export preserves every original Source Dataset column with predictions and traceability evidence.
- Accepted Source Review evidence hierarchy: the untouched CSV remains primary; a concise Transformation Audit reports alignment, mappings, missing values, defaults, and warnings; on-demand Model Input Evidence compares a selected raw value with what CatBoost and LightGBM receive. Do not display a second 351-column processed table by default.
- Accepted missing-column policy: the Inference Contract classifies every Model Feature as Required or Omissible. An absent Required Model Feature blocks a Verified Run. An absent Omissible Model Feature uses only its predeclared missing representation, with a prominent warning, Transformation Audit entry, and explicit operator confirmation. This policy must be validated before release rather than improvised on final data.
- Accepted persistence policy: completed Prediction Runs persist in a local Run Archive with results, model/contract identity, threshold, checksums, validation findings, and Transformation Audit. The full Source Dataset is copied into a self-contained Source Snapshot only through visible opt-in; otherwise, the archive records its path and checksum and reports later absence or change.
- Accepted results-summary direction, subject to hands-on refinement: use one calm two-level Run Summary, not a KPI-card grid. Lead with completion and processed-row count; present class counts, component disagreement, and warning count as a readable secondary sequence; keep model version, threshold, and runtime quiet or behind details. Use color only for meaningful state or warnings. The exact first cohort-investigation surface is being revised because a thousands-row table cannot be the main exploration method.
- Accepted primary analysis visualization: the secondary Analysis view leads with one interactive Ensemble Score Distribution, marks the Release Threshold, and lets score-range selection filter the results table. On unlabeled data it must not imply observed performance or calibration.
- Accepted second and final default cohort visualization: a separate Component Agreement Plot compares CatBoost and LightGBM scores, supports linked table selection, and switches to density-aware rendering for large cohorts. It investigates model disagreement but must not be presented as evidence of accuracy.
- Accepted Ground-Truth Authorization: detecting a label-like column never enables metrics automatically. The operator selects the ground-truth column, confirms its binary mapping, reviews valid/missing/unrecognized counts, and explicitly authorizes Evaluation. Labels remain excluded from inference. Partial-label metrics use only the Evaluated Cohort and prominently disclose its size versus the full Result Set.
- Accepted identity policy: immutable Source Row identity always exists. `Variant_ID` is the default visible Record Identifier when present; otherwise, the operator may map another Context Column or use generated display-only `ROW-000001` values. Duplicate identifiers are preserved with warnings. Generated identifiers permit prediction but cannot silently satisfy a required Competition Export field.
- Accepted desktop architecture, conditional on visual quality: PySide6 with a custom QML/Qt Quick presentation layer and a direct Python inference core. Package with `pyside6-deploy`/Nuitka after target-OS validation. The app must not ship with generic/default Qt styling. Qt/module licensing remains a release gate, and GPL-only optional modules such as Qt Graphs are excluded until the public license is deliberately chosen.
- Accepted first-release build matrix: produce and test native Linux and Windows packages. macOS is deferred unless a concrete Computational Health Lab need emerges.
- Confirmed brand starting state: **Computational Health Lab** is the established organization/laboratory name, but there is currently no logo, symbol, official palette, or typography system.
- Accepted brand architecture: Computational Health Lab is the creator, owner, and primary Laboratory Identity. Build a reusable symbol, complete wordmark, and adaptable lockups for future lab work. `Variant Inference` is a provisional functional Product Descriptor, not a separate commercial brand; reconsider a distinct product name only after the working application demonstrates a need. Avoid cliché DNA, cross, heartbeat, and AI-brain marks.
- Confirmed identity scope: the laboratory will join other competitions and undertake projects beyond missense-variant prediction. The Laboratory Identity must therefore remain a broad computational-health umbrella and must not encode this model or competition as the lab's permanent subject.
- Accepted Laboratory Thesis: **“Computational Health Lab turns complex health data into transparent, testable computational evidence.”** Future identity work should express complexity becoming clarity, traceability, and scientific rigor without relying on literal disease, DNA, or algorithm imagery.
- Accepted naming system: public wordmark and attribution use **Computational Health Lab** without hyphens. `CHL` is a secondary compact monogram only. Preserve `Computational-Health-Lab` solely where an official competition system requires the registered team name.
- Accepted leading logo direction: explore an abstract evidence symbol showing complex inputs becoming ordered, traceable structure. It must work at app-icon size and in monochrome and pair with the full wordmark. Include one strong CHL-based challenger before final selection; geometry and color are not yet decided.
- Accepted primary visual environment: light-first for laboratories, competition rooms, projectors, reports, and print, with mandatory black-and-white logo performance. Dark mode is deferred until it can be designed as a full secondary system rather than an inversion. Exact palette remains undecided.
- Rejected visual round: the initial comps combined laboratory identity and application UI too early. Lattice Resolve looked the most normal but still felt like generic administrative software and its symbol was decorative; CHL Proofmark, Evidence Signal Bench, and the standard dashboard were rejected. None is approved for implementation.
- Accepted visual-development reset: design and approve the Computational Health Lab symbol/wordmark/monochrome/icon system first, then design the application as a separate round inheriting that identity and the already confirmed workflow.
- Final logo decision on August 27, 2026: the user explicitly locked the **original full-color Resolved Layers** concept as the final Laboratory Identity direction. The approved reference includes its three open overlapping forms, blue/black/gray treatment, complete `Computational Health Lab` wordmark relationship, and overall presentation character. Evidence Gate was not preferred; CHL Structure is rejected because it reads like a clothing-brand logo. The later monochrome Calibrated Original, Essential Layers, and Evidence Cell sheets are unselected explorations and must not replace the original. Production vectorization remains required but must faithfully reconstruct the approved reference rather than reopen or reinterpret the concept.
- Approved Source Review visual direction: **Split Evidence Desk hybrid v2**. It keeps the raw source table beside a persistent evidence pane, uses a light application bar with the full-color Resolved Layers symbol and complete Computational Health Lab wordmark, provides one compact `Run Archive` command, removes the Dossier's confusing date-filter sidebar, keeps model compatibility inside Inference Contract Fit, and requires an explicit confirmation checkbox. The user considered compacting the right pane but confirmed that the full Source Identity, Inference Contract Fit, Transformation Audit, and Confirm & Run sections may remain visible because they are organized and support verification.
- Source Review requires explicit operator confirmation before a Prediction Run begins.
- The application is not merely an upload-and-predict shell. Its post-prediction Investigation Workspace must support studying both cohort-level patterns and individual Variant Records with useful filtering, detail views, and carefully justified graphics.
- Official output is represented by an immutable Verified Run using the Production Model's locked Inference Contract and threshold.
- Controlled threshold experimentation is allowed only in a separate Analysis Sandbox derived from a Verified Run. It cannot overwrite the Verified Run or produce Competition Export.
- Confirmed hierarchy correction: a row-preserving table cannot be the primary investigation surface for a Result Set containing roughly 4,000–10,000 variants. The initial post-prediction experience must orient the operator at cohort level and provide meaningful ways to narrow the Result Set. The full table lives in a separate `Records` tab for search, sorting, grouping, filtering, exact verification, export, and drilling into selected variants. Entering `Records` from a cohort selection preserves the active cohort filters. Source Row identity and official export order remain stable everywhere.
- Confirmed cohort-to-record interaction: selecting a score range, investigation category, or other cohort subset does not navigate immediately. The workspace shows the resulting count and an explicit contextual action such as `Inspect 126 records`; only that action opens the `Records` tab with the selection represented as visible, removable filters.
- Confirmed cohort-overview composition: the Ensemble Score Distribution is the one visual centerpiece. A single compact `Investigation Sets` list sits beside it with Near Release Threshold, Model Disagreements, Warnings, Predicted Pathogenic, and Predicted Benign. The Component Agreement Plot remains in its separate `Model agreement` view; the overview does not become a multi-chart dashboard.
- Confirmed information-architecture priority: the application may use multiple focused panels when that keeps each task clean. Competition-relevant evaluation is first-class rather than buried beneath modern investigation features. F1 and related observed metrics belong in a dedicated label-dependent Evaluation panel; an unlabeled final competition run cannot calculate them. Saved model-release validation evidence must remain clearly distinct from metrics calculated on the current Prediction Run.
- Confirmed competition-scoring boundary: TEKNOFEST keeps the final test labels private. The application runs inference on the unlabeled final CSV and produces the ordered Competition Export; the organizers compare those predictions with their private Ground Truth to calculate TP, FP, FN, F1, and any supplementary metric such as MCC. The exact submission schema and transfer mechanism remain unpublished and must not be guessed. The final run should therefore report that it is ready/awaiting organizer scoring, not display a fabricated current-run F1.
- Confirmed panel separation: label-dependent `Evaluation` and unlabeled `Competition Submission` are different workspaces. Evaluation requires Ground-Truth Authorization and shows local observed metrics. Competition Submission validates and exports a Verified Run for external Organizer Scoring and never shows F1. Organizer format details will be added later through a versioned Competition Export Profile supplied from the official instructions; until then, the submission panel reports `Organizer format pending` and must not present a guessed CSV as official.
- The first release must remain smooth through 10,000 variants on the competition laptop. Larger-scale claims require end-to-end benchmarking.
- When the operator enters record-level investigation and selects a variant, use a resizable split workspace: the filtered/searchable records table remains visible and a Variant Inspector opens beside it. The inspector can expand for deeper study without losing Source Row context.
- Confirmed explanation feature: the Variant Inspector will compute Model Contributions on demand. CatBoost and LightGBM explanations remain separate and are presented as model behavior, not biological causation or clinical evidence.
- Confirmed AI authority boundary: the optional AI Investigation Assistant is technically read-only and separate from deterministic inference. It may query evidence and propose filters, charts, selections, or sandbox actions, but cannot execute changes or alter a Source Dataset, Verified Run, Release Threshold, Inference Contract, or Competition Export.
- AI and internet integration is intentionally deferred until the core application is reliable. The initial architecture should remain integration-friendly, but current product grilling and implementation should not spend time designing the assistant. Core inference remains local and offline.
- The reported 0.61 Decision Threshold is not intrinsic to CatBoost, LightGBM, or the ensemble. It was selected using the current held-out predictions and is therefore tied to that model release, sample, and class distribution. Because the same held-out set was used for threshold selection and reported evaluation, 0.61 needs stronger out-of-fold or dedicated-validation evidence before being treated as final-stage robust.
- The final competition labels are hidden, so the application cannot calculate final-data F1 or determine the best threshold during the competition. F1, precision, recall, FP, and FN require ground truth. A Threshold Study is permitted only for a labeled evaluation dataset; an unlabeled Analysis Sandbox may show classification changes but cannot identify an optimal threshold.
- Threshold Study is now confirmed to be enabled only when verified ground-truth labels are present. Unlabeled competition runs must use a Release Threshold fixed before the final data arrive.
- `Release Threshold` does not mean 0.50 or 0.61 specifically. The current 0.61 value remains a provisional candidate because it has more direct evidence for the current saved model than the numerical midpoint 0.50, but the final value must come from stronger validation and may be neither.
- Replace the loose phrase "Benign-heavy threshold study" with **Target-Prevalence Study**. This uses labeled out-of-fold predictions and reweights/resamples them to the organizer's approximate final class ratio before the final. It cannot discover the true best threshold for hidden-label data and is informative only if class-conditional model behavior transfers.
- Confirmed strategy, not yet executed: perform the Target-Prevalence Study in the parent training repository before freezing the competition Release Threshold. Use it to confirm or replace provisional 0.61, document assumptions, then bundle the selected value in the Inference Contract.
- Trust, evidence, and reproducibility take priority over decorative analytics.

## 4. Current workflow hypothesis

The leading direction is a persistent Run Workspace rather than a sequence of disconnected upload and dashboard pages:

1. A compact `Open CSV` command selects the Source Dataset.
2. The workspace presents Source Evidence and schema-validation findings.
3. The operator explicitly confirms the reviewed Source Dataset.
4. Prediction runs only against a normalized copy that follows the Inference Contract.
5. The Result Set remains traceably connected to the Source Dataset and model version.
6. The Investigation Workspace supports cohort-level and individual-variant study without visual overload.

This hypothesis is not fully accepted until the remaining grilling questions are answered.

## 5. Open decisions

- Define and approve a cohort-first post-prediction workspace that helps operators narrow thousands of variants before opening the on-demand Records table and Variant Inspector.
- Which visualizations materially aid verification and which should be omitted.
- Run Archive retention, secure deletion, and Source Snapshot encryption requirements.
- Offline-only versus optional hosted deployment.
- Production vector assets and usage rules for the approved Resolved Layers identity; the public application name remains undecided and must be distinctive enough for a future public open-source release.
- Accessibility target and supported languages.
- License for application source code.
- Whether organizer agreements permit publishing trained weights, feature schema, categorical mappings, or example data.
- Whether organizers permit changing the PDR-reported threshold or retraining the model before the final.
- Deferred AI assistant questions: external-data boundary, consent model, retention requirements, and local-provider support.

## 6. Where work stopped

The first implementation milestone was completed on August 28, 2026. The repository now contains a runnable PySide6/QML desktop foundation and the approved Split Evidence Desk hybrid v2 Source Review vertical slice. The custom light-first shell uses the complete Computational Health Lab identity by cropping the locked full-color raster reference at runtime; it does not introduce replacement logo geometry. Production vectorization remains unresolved.

Implemented behavior:

- Compact native CSV selection, exact Source Identity evidence, and a faithful read-only raw preview.
- A QML `TableView` that creates only visible delegates over a Python `QAbstractTableModel`; the CSV adapter stores rows in an ephemeral SQLite file and keeps a bounded 1,024-row page cache. The core path was tested with a synthetic 10,000-row CSV.
- SHA-256, delimiter, encoding, last-modified time, dimensions, immutable one-based Source Row identity, sampled raw type labels, and cleanup of the temporary review store.
- Integrity-checked JSON Model Package manifests with relative artifact-path validation and SHA-256 verification. The application does not deserialize arbitrary model uploads or loose pickle folders.
- An immutable Inference Contract domain model with explicit Required/Omissible presence policy, feature order, numeric/categorical handling, category mappings, ensemble weights, Release Threshold, and a no-row-filtering constraint.
- Inference Contract Fit separating absent Required Model Features, absent Omissible Model Features, surplus Context Columns, duplicate-name blockers, blocking issues, and warnings.
- Transformation Audit summaries for normalized-copy type handling, missing-value policy, fixed category mappings, contract alignment, and preserved row order.
- Explicit operator confirmation gating. A compatible reviewed source is necessary but not sufficient; the run action activates only after confirmation, and opening a replacement source clears the prior confirmation.
- Separate typed application ports for deterministic inference, Run Archive persistence, Evaluation, Competition Export Profiles, and future read-only investigation evidence so those capabilities do not leak into QML.
- A reproducible `pyproject.toml`, isolated `.venv` workflow, synthetic non-organizer fixture, README run/test instructions, 11 passing non-visual tests, Python compilation, and clean headless QML startup/render checks.

The first slice deliberately stops before prediction. The enabled action records that Source Review is complete and states that the deterministic inference adapter is the next milestone; it does not create a fake Verified Run. No real Model Package manifest, trained weights, organizer-derived category mappings, organizer rows, or machine-specific parent path were copied into committed defaults. The bundled synthetic fixture is development-only and cannot perform inference.

An independent manager acceptance review on August 28, 2026 reran all 11 tests, the offscreen QML smoke check, and Python compilation successfully and visually inspected the 1536×980 Source Review render. The milestone has no blocking acceptance issue. Production vectorization and tighter wrapping of long evidence values in the narrow pane remain non-blocking polish work.

The independent repository now has a clean `main` baseline with three logical commits rather than one bulk snapshot: product memory and visual direction; Source Review domain/evidence adapters; and the PySide6 desktop shell. Temporary design-tool process logs, virtual environments, generated caches, real model artifacts, and organizer data are excluded. The committed state was revalidated with all 11 tests and the offscreen smoke check. A private GitHub remote is planned, but creation is pending explicit confirmation that the authenticated `Abdourahman1909` account is the intended destination.

The first post-prediction Results workspace comp at `.impeccable/mocks/app/results-workspace-v1.png` is a superseded exploration rather than an approval candidate. Its useful semantics were carried forward, but its dominant table used the wrong hierarchy for 4,570 variants.

The revised cohort-first comp is `.impeccable/mocks/app/cohort-overview-v1.png`. It preserves the approved shell, opens with a compact Verified Run summary, makes the Ensemble Score Distribution the only main visualization, places one compact Investigation Sets list beside it, and uses an explicit `Inspect 184 records` transition into the separate filtered `Records` tab. No table or Variant Inspector appears on Overview. Its overview composition remains the leading reference, but its navigation is now incomplete: the confirmed architecture separates label-dependent Evaluation from unlabeled Competition Submission. The comp is not approved for implementation.

Next practical focus: define the distributable immutable Model Package manifest for the real CatBoost–LightGBM release without committing restricted artifacts, implement the deterministic inference adapter against that validated package, produce ordered results with Source Row identity, and persist the first immutable Verified Run manifest. Before building any post-prediction navigation, resolve and approve the focused navigation that separates Overview, Records, Model agreement, Evaluation, and Competition Submission while keeping `Organizer format pending` until official instructions arrive.

## 7. Authoritative files

1. `docs/adr/` for accepted architectural decisions.
2. `CONTEXT.md` for canonical product language.
3. `docs/PRD.md` for current product requirements and unresolved questions.
4. `docs/PROJECT_MEMORY.md` for consolidated context and stopping point.
5. The parent repository's saved model objects and `ensemble_config.pkl` for actual model parameters.
6. The parent repository's competition held-out dataset and predictions for reported metrics.

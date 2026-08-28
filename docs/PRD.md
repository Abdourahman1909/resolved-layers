# Resolved Layers — Product Requirements

**Status:** Draft — active product grilling

## Purpose

Create a focused, trustworthy application that lets an operator select a compatible CSV, verify the exact source, run Computational Health Lab's Production Model, investigate cohort-level and individual-variant results, and export reproducible outputs.

The competition is the first demanding deployment context, not the product's permanent boundary. The application should remain useful for later research datasets that provide richer variant features or metadata.

## Intended users

- Computational Health Lab team members operating the model at the TEKNOFEST final.
- Competition judges verifying the submitted source and observed execution.
- Research users investigating compatible variant datasets after the competition, if publication and licensing allow distribution.

Non-technical clinical use has not been approved. The product and its outputs are for research and education, not diagnosis or treatment.

## Product principles

1. **Evidence before prediction.** The operator can verify the exact Source Dataset before trusting a Result Set.
2. **One package per run.** Every Prediction Run fixes one validated Model Package whose artifacts cannot drift from preprocessing, feature order, mappings, weights, or threshold.
3. **Focused over busy.** Every visible metric or visualization must support verification, interpretation, or export.
4. **Reproducible by construction.** Every Prediction Run identifies its source, model, configuration, and output.
5. **Local confidence.** Competition-critical inference must not depend on internet access or external services.
6. **Professional restraint.** The desktop interface must feel intentionally designed, calm, and immediately understandable; default toolkit styling and generic dashboard patterns are not acceptable release quality.
7. **Laboratory before competition.** The identity must remain credible across future Computational Health Lab competitions and projects rather than encoding this one prediction task.
8. **Complexity into evidence.** The laboratory identity should express the accepted thesis that complex health data becomes transparent, testable computational evidence.
9. **Competition metrics remain first-class.** Modern investigation features must not bury F1 or other authorized evaluation evidence. Multiple focused panels are preferred over forcing unrelated tasks into one crowded surface.
9. **Symbol before acronym.** Resolved Layers is the final approved Laboratory Identity direction after comparison with an abstract gate, a CHL monogram, and three same-concept refinements. Preserve the original full-color symbol and complete wordmark; production vectorization may correct technical construction but must not redesign the approved appearance.

## In scope

- Compact CSV selection inside a persistent workspace.
- Source Evidence: filename, checksum, dimensions, columns, and faithful raw-data inspection.
- Inspection of every column supplied by the Source Dataset, including columns that are not consumed by the Production Model.
- Mandatory operator confirmation after Source Review and before prediction begins.
- Strict Inference Contract validation.
- Clear blocking errors and non-blocking warnings.
- Deterministic local batch inference.
- Ordered binary predictions.
- An Investigation Workspace for cohort-level patterns and individual Variant Records.
- On-demand per-variant Model Contributions, with CatBoost and LightGBM explanations kept separate and explicitly described as model behavior rather than biological causation.
- Focused filtering, comparison, and justified graphical analysis that supports investigation without visual overload.
- An Analysis Sandbox for comparing alternative decision thresholds without modifying the Verified Run.
- Competition Export and a detailed reproducibility export.
- Model version and integrity information.
- An architecture capable of hosting a local Model Library of validated Computational Health Lab Model Packages, while initially shipping only the current CatBoost–LightGBM package.
- A local Run Archive that restores completed runs across application restarts.
- Research-use limitation and licensing information.

## Out of scope

- Model training and hyperparameter tuning.
- Ablation studies and experimental evaluation.
- Arbitrary model-file or model-folder loading.
- Installing or selecting additional Model Packages in the first core release; this follows after the single-package workflow is reliable.
- Unrestricted decision-threshold editing.
- Using exploratory threshold results as official predictions or Competition Export.
- Clinical diagnosis, treatment, or medical decision support.
- Organizer-data publication without written permission.

## Draft workflow

### Run Workspace

The application opens into a working surface, not a large upload prompt. A compact `Open CSV` command selects the Source Dataset.

The first release opens with its bundled Model Package already fixed. The architecture nevertheless treats the model as a validated package rather than hard-coded loose files. A later Research Mode may select from an installed Model Library before Source Review; once a Prediction Run begins, its Model Package cannot change. Competition Mode always locks the designated official package.

### Source Review

The workspace replaces its empty state with Source Evidence and validation findings. The untouched raw rows remain the primary evidence and are directly inspectable. Column order is not treated as meaningful; the inference layer aligns features through the Inference Contract. Prediction cannot begin until the operator explicitly confirms the reviewed Source Dataset.

Source Review includes a concise Transformation Audit covering feature reordering, categorical mappings, missing values, supplied defaults, and warnings. It does not render a second full-width copy of hundreds of processed columns. When deeper verification is needed, the operator can request Model Input Evidence for a selected row or feature and compare the raw value with the representation supplied separately to CatBoost and LightGBM.

### Prediction Run

The Production Model operates on a normalized representation derived from the Source Dataset. The source remains unchanged and traceable. A run produced with the approved Inference Contract is stored as an immutable Verified Run.

Completed runs persist locally in the Run Archive with their predictions, Model Package identity, Inference Contract and threshold identity, checksums, validation findings, and Transformation Audit. The archive does not silently duplicate the complete Source Dataset. Creating a self-contained Source Snapshot requires a visible opt-in; without one, the archived run retains the original path and checksum and reports if the source later becomes unavailable or no longer matches.

### Result Set

Predictions remain connected to Source Row identity and order. Immediately after completion, the Investigation Workspace opens at cohort level with a compact Run Summary and focused ways to understand and narrow the Result Set. It must not expect an operator to investigate thousands of variants by manually browsing rows. The complete row-preserving table lives in a separate on-demand `Records` tab for targeted search, sorting, grouping, filters, exact verification, export, and record-level drill-down. Opening `Records` from a cohort selection carries that selection forward as visible active filters. The workspace supports both cohort-level analysis and detailed study of individual Variant Records without becoming a dashboard of decorative charts.

The Run Summary is one calm, two-level information band rather than a grid of oversized metric cards. Its primary line states whether the run completed and how many variants were processed. A secondary line presents Pathogenic and Benign counts, model-disagreement count, and validation-warning count as one readable sequence. Model Package version, Release Threshold, and runtime are visually quieter or available through `View details`.

The initial summary contains no chart. Color is sparse and semantic, reserved for state and warnings rather than decorating every number. When verified labels exist, label-dependent metrics remain in a separate Evaluation view; they never appear for an Unlabeled Prediction Set.

The cohort investigation experience uses one interactive Ensemble Score Distribution rather than a chart grid. It shows the cohort across the zero-to-one score range, marks the applicable Release Threshold, and supports selecting a score interval to narrow the Result Set before opening or updating the Records surface. It may identify predictions near the decision boundary but must not describe score shape as observed accuracy, calibration, or F1 when labels are absent.

Cohort selections are reversible and do not trigger surprise navigation. After selecting a chart region or investigation category, the workspace displays the selected count and an explicit contextual action such as `Inspect 126 records`. Activating that command opens the separate `Records` tab with the cohort selection carried forward as visible, removable filters.

The only second default cohort visualization is a Component Agreement Plot comparing CatBoost and LightGBM scores. It lives in a separate `Model agreement` view, shows agreement around the diagonal and disagreements across component decision boundaries, and links point or region selection back to the results table. Large cohorts use density-aware rendering to avoid unreadable overplotting. It must not be presented as evidence of model accuracy.

When opened, the Records table remains deliberately compact: source identity, prediction, Ensemble Score, component-model agreement, and validation warnings. It supports useful single- and multi-column sorting, grouping by meaningful categorical/result fields, focused filters, direct identifier search, and exact verification of selected Variant Records. Searchable column controls let the operator add any Model Feature or Context Column from the Source Dataset without forcing hundreds of columns into the view. The Variant Inspector provides the complete row-level view of all original columns. Grouping and sorting are reversible views over the immutable Result Set and never rewrite Source Row identity or Competition Export order.

The table implementation must remain responsive without rendering the entire Result Set into the visible interface at once. Sorting and filtering must never alter Source Row identity or the order used for Competition Export.

Selecting a row in the Records surface opens a resizable Variant Inspector beside the table instead of navigating away. The filtered table remains visible for movement between relevant variants and preservation of the narrowed cohort context. The inspector may expand when more space is needed for detailed investigation.

### Analysis Sandbox

The user may derive an Analysis Sandbox from a Verified Run and compare how alternative decision thresholds change classifications and cohort-level summaries. Sandbox state is visually and semantically distinct, cannot overwrite the Verified Run, and cannot produce a Competition Export.

When verified ground-truth labels are present, a Threshold Study may calculate F1, precision, recall, FP, FN, MCC, and other evaluation metrics for alternative thresholds. For an Unlabeled Prediction Set, the sandbox may show only how predicted classifications and score distributions change; it must not recommend a "best F1" threshold or display label-dependent metrics.

Evaluation is a dedicated focused panel rather than a collection of metric cards mixed into the unlabeled cohort Overview. F1 is the primary observed metric for the competition context; precision, recall, MCC, AUPRC, and the confusion matrix provide supporting evidence. Error subsets link to the filtered Records surface for exact FP/FN inspection. Metrics calculated from authorized labels for the current Prediction Run must never be confused with saved validation evidence attached to the Model Package.

For the TEKNOFEST final, the application receives an Unlabeled Prediction Set and produces a Competition Export; TEKNOFEST retains the private Ground Truth and calculates the official F1 and any supplementary metrics externally. The app must clearly show `Ground truth unavailable` / `Awaiting organizer scoring` for that run and must not calculate or imply official performance. The Competition Export validator must preserve every required identifier/row and exact source order, but the concrete submission schema remains an unresolved organizer dependency until officially published.

### Competition Submission Workspace

Competition submission is a separate panel from Evaluation. In Competition Mode, an unlabeled Verified Run exposes a Competition Submission Workspace that shows readiness for external scoring, the active Competition Export Profile and version, row/identifier coverage, prediction encoding, source-order preservation, duplicate/missing checks, output preview, checksum, and export validation. It contains no F1, confusion matrix, or other label-dependent metric.

The exact organizer format must be represented as a versioned Competition Export Profile rather than hard-coded assumptions throughout the interface. The profile defines required columns and names, identifier and row-order rules, Pathogenic/Benign encoding, filename, delimiter, and any organizer-specific constraints. Until TEKNOFEST publishes those details, the panel must visibly report `Organizer format pending`; an internal prediction export may remain available, but it must not be labelled an official Competition Export.

The Evaluation Workspace remains a distinct label-dependent panel. It becomes available only after Ground-Truth Authorization and calculates metrics locally for the disclosed Evaluated Cohort. The Competition Submission Workspace instead packages predictions for Organizer Scoring against private labels. Both may exist in the architecture, but they must never share status language or imply that successful export validation is model-performance validation.

Evaluation never activates merely because a label-like column is detected. During Source Review, the operator must complete Ground-Truth Authorization by selecting the reference-label column, confirming its Pathogenic/Benign value mapping, reviewing valid, missing, and unrecognized counts, and explicitly enabling Evaluation. The authorized label column is excluded from model input.

Partially labeled datasets may be evaluated only on their Evaluated Cohort. Every metric surface and export must prominently state the evaluated numerator and total row count, such as `842 of 1,000 variants`, and must not imply that unlabeled or invalid rows contributed to observed performance.

The Release Threshold is selected and fixed before unlabeled competition data are received. The numeric midpoint 0.50 is a baseline, not an inherently neutral or reliable threshold. Until a stronger Threshold Study is completed, 0.61 remains the provisional candidate associated with the reported Production Model rather than a universally valid cutoff.

A Target-Prevalence Study may inform the Release Threshold by reweighting or resampling labeled out-of-fold predictions to an expected class ratio. It must be presented as a scenario estimate with explicit transfer assumptions, never as measurement of the hidden final labels.

Before the competition release is frozen, the team will perform this study in the parent training repository and use its evidence to confirm or replace the provisional 0.61 Release Threshold. The selected value and study assumptions must be recorded in the released Inference Contract.

## AI and internet integration

**Release status:** deferred. The first implementation should preserve clean extension boundaries for later AI and internet integration, but the assistant itself is not a current delivery priority.

- The deterministic local inference workflow must remain fully functional without internet or AI access.
- A future AI Investigation Assistant may query application evidence through typed, read-only tools, summarize selected results, explain documented metrics, and help users navigate investigations.
- AI output must never alter a Verified Run, Release Threshold, Source Dataset, Inference Contract, or Competition Export.
- The assistant may propose a filter, selection, chart, or Analysis Sandbox action, but execution requires explicit approval through the normal deterministic application workflow.
- No complete CSV, restricted organizer data, or genetic record should leave the device by default. Any external transmission requires a visible preview, explicit operator consent, and a documented retention/privacy policy.
- Internet literature lookup must be a separate user-authorized action and must not silently attach source rows or model artifacts.
- AI-generated interpretation must be labeled as generated assistance, grounded in cited application evidence, and prohibited from presenting diagnosis or treatment advice.

### Export

The application creates two intentionally different outputs:

- a minimal Competition Export containing only the ordered fields required for organizer scoring;
- a Research Export preserving every original Source Dataset column alongside predictions and traceability evidence.

A detailed run manifest records model version, configuration identity, source checksum, row count, runtime, and output checksum.

## Validation policy — draft

- Different column order: reorder internally through the Inference Contract.
- Context Columns: exclude from prediction, keep inspectable, and preserve in the Research Export.
- Missing Required Model Feature column: block the Verified Run.
- Missing Omissible Model Feature column: supply the Inference Contract's declared missing representation (`NaN`, `Unknown`, or another explicitly versioned value), show a prominent warning, record it in the Transformation Audit, and require explicit operator confirmation.
- Feature presence classifications must be validated and frozen in the Inference Contract before release; the application cannot improvise them from an incoming CSV.
- Missing numeric value: preserve as missing for native model handling.
- Unknown categorical value: map to `Unknown` and report a warning.
- Missing `_panel`: supply `Unknown` and report it.
- Source Row: always assign and preserve immutable positional identity independently of any identifier column.
- `Variant_ID` present: use it as the default Record Identifier; preserve duplicates and warn without changing row order.
- `Variant_ID` absent: let the operator map another Context Column as the Record Identifier or generate display-only values such as `ROW-000001` without modifying the Source Dataset.
- Generated Record Identifiers: permit prediction and investigation but never silently satisfy a Competition Export field. If the organizer schema requires a real identifier and none is mapped, block that export.
- Label-like columns: never use as inference features; require Ground-Truth Authorization before any observed metric is calculated.
- Label-dependent evaluation and threshold optimization: available only when verified ground-truth labels are explicitly present.
- Partial labels: evaluate only the Evaluated Cohort and prominently disclose its size relative to the complete Result Set.
- Unlabeled prediction: use the Release Threshold from the Inference Contract and disable all observed-performance claims.

## Verification requirements

Each Prediction Run should be able to expose:

- Source filename and SHA-256 checksum.
- Raw row and column counts.
- Inference Contract version and checksum.
- Model Package identity, Production Model version, and artifact checksums.
- Decision threshold and ensemble weights.
- Start time, completion time, and duration.
- Output row count and checksum.
- Validation warnings and transformations applied.

## Performance target

- The first release must remain smooth through 10,000 variants on the competition laptop.
- Larger cohorts should be architecturally possible, but no 50,000+ claim is made until end-to-end model, memory, table, filtering, and export benchmarks pass.
- Large tables must use virtualization or lazy retrieval and must never change Source Row identity or Competition Export order.

## Desktop architecture

- Presentation layer: PySide6 with QML/Qt Quick and a custom application design system.
- Inference core: Python, reusing CatBoost, LightGBM, pandas, NumPy, and the deterministic prediction behavior directly rather than introducing a browser-hosted server or separate language bridge.
- Packaging direction: `pyside6-deploy`/Nuitka, validated on every supported target operating system before release.
- First-release build matrix: native Linux and Windows packages, each tested on its target OS. macOS packaging is deferred until a concrete lab requirement exists.
- Visual quality gate: the application must not ship with an unmodified default Qt control appearance. Technology acceptance is conditional on delivering the professional, quiet, evidence-first interface established in this PRD.
- Primary visual environment: light-first for bright rooms, projectors, reports, and print; the Laboratory Identity must also work in pure monochrome. Dark mode is deferred until it can be designed and tested as a complete secondary system.
- Licensing gate: confirm compliance for PySide6/Qt and every optional module before public release. Do not introduce GPL-only optional modules such as Qt Graphs until the application license is deliberately chosen; the two required charts must use a license-compatible implementation.

## Visual-development sequence

Laboratory Identity and application-interface direction are separate approval rounds. First establish and approve the Computational Health Lab symbol, wordmark, monochrome behavior, and compact icon behavior. Only then create application comps that inherit the approved identity and express the confirmed operational workflow.

The first combined identity/application concept round was rejected. Its Lattice Resolve screen was the only remotely plausible option but still felt like ordinary administrative software, its mark read as decorative, and the other metaphor-heavy directions did not feel like the intended application. None of those comps is approved implementation guidance.

The subsequent logo-only comparison selected **Resolved Layers** because of the symbol's shape and perceived uniqueness. Evidence Gate was not preferred, and CHL Structure was rejected because it resembled a clothing-brand mark. After reviewing Calibrated Original, Essential Layers, and Evidence Cell refinements, the user explicitly returned to and locked the **original full-color Resolved Layers concept** as the final identity direction, including its shape, blue/black/gray treatment, wordmark relationship, and overall appearance. The refinement sheets are unselected explorations. A faithful production vector package remains to be authored; that work must reproduce rather than reinterpret the approved reference.

For Source Review, use the approved Split Evidence Desk hybrid v2 structure: the raw source table remains visible beside a persistent evidence pane containing Source Identity, Inference Contract Fit, Transformation Audit, and explicit run confirmation. Retain these four organized sections in the default pane rather than collapsing successful details solely to save space; this is an evidence-oriented competition and research surface. The application bar uses the full-color Resolved Layers symbol and complete Computational Health Lab wordmark on a light surface. Do not add date-based Run Archive filters to the Source Review navigation. If archive access appears here, expose it as one compact `Run Archive` command. Keep model-package compatibility inside Inference Contract Fit, where its meaning is visible.

## Open decisions

1. Public-release and licensing boundaries.
2. Production vectorization of the approved Resolved Layers identity and the separate application visual system.
3. Accessibility and localization.
4. Whether organizers permit changing the reported threshold or retraining the Production Model between PDR submission and the final.
5. Model Package installation format, trusted publisher policy, and the release in which Research Mode exposes Model Library selection.
6. Run Archive retention controls, deletion workflow, and whether sensitive Source Snapshots require application-level encryption.

Deferred AI decisions, to revisit after the core application is reliable:

- Which evidence may be transmitted to external AI providers, under what consent and retention controls.
- Whether a local AI provider and external providers share one adapter interface.

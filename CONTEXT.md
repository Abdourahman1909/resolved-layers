# Resolved Layers

This context defines the language used by Computational Health Lab's standalone missense-variant inference product.

## Language

**Laboratory Identity**:
The shared Computational Health Lab name, symbol, wordmark, and visual system that identifies the creators across applications, models, reports, and research.
_Avoid_: App logo, competition-team skin, personal branding

**Laboratory Display Name**:
`Computational Health Lab`, written without hyphens, is the canonical public name used in the wordmark and product attribution.
_Avoid_: Computational-Health-Lab, The Computational Health Lab, CHL as the primary name

**Laboratory Monogram**:
`CHL`, a secondary compact identifier reserved for spaces where the Laboratory Display Name cannot fit. It does not replace the complete public name.
_Avoid_: Primary wordmark, product name, unexplained acronym

**Laboratory Thesis**:
Computational Health Lab turns complex health data into transparent, testable computational evidence.
_Avoid_: Slogan, marketing promise, variant-prediction mission

**Product Name**:
`Resolved Layers`, the distinctive public name of this application and repository. It is presented as a product created by Computational Health Lab and can encompass future validated Computational Health Lab Model Packages beyond the initial competition model.
_Avoid_: Variant Inference App, CHL Resolve, generic evidence dashboard

**Product Descriptor**:
The functional title `Variant Inference` used beneath `Resolved Layers` to describe the current missense-variant workflow without limiting the future product name.
_Avoid_: Product name, laboratory name, commercial codename

**Production Model**:
The approved model represented by the Model Package selected and fixed for a Prediction Run. The initial TEKNOFEST release uses the current CatBoost and LightGBM ensemble.
_Avoid_: Loose model file, active pickle

**Model Package**:
A versioned, integrity-checked release containing model artifacts and the complete Inference Contract needed to reproduce their predictions.
_Avoid_: Model file, uploaded pickle, weights folder

**Model Library**:
The local collection of installed and validated Model Packages available to authorized research workflows. It never treats arbitrary model files as runnable packages.
_Avoid_: Model-folder browser, arbitrary model upload

**Competition Mode**:
A restricted operating context that fixes the official Model Package and preserves the verified competition workflow.
_Avoid_: Demo mode, locked UI

**Research Mode**:
An operating context that may select among installed Model Packages and compatible Source Datasets while preserving run-level traceability.
_Avoid_: Anything-goes mode, training mode

**Inference Contract**:
The immutable definition inside a Model Package that binds its model artifacts to their required feature order, categorical mappings, missing-value behavior, ensemble weights, decision threshold, version, and integrity metadata.
_Avoid_: Model settings, app configuration

**Ensemble Score**:
The Production Model's continuous value between zero and one used to rank variants and apply a Decision Threshold. It must not be presented as a universal clinical probability unless calibration is separately demonstrated.
_Avoid_: Certainty, disease probability

**Decision Threshold**:
The cutoff that converts an Ensemble Score into Pathogenic or Benign. It is selected from validation evidence for a specific Production Model release and expected data distribution; it is not an intrinsic parameter learned by the component models.
_Avoid_: Model confidence, natural cutoff

**Release Threshold**:
The Decision Threshold fixed in the Inference Contract before an Unlabeled Prediction Set is received. It may be 0.61, 0.50, or another validated value; "locked" describes when it becomes immutable, not which numeric value is chosen.
_Avoid_: Pre-locked threshold, default threshold, final-data threshold

**Threshold Selection Set**:
The labeled predictions used to choose a Decision Threshold. Performance measured on the same set is optimization evidence, not an independent estimate of generalization.
_Avoid_: Final test set, unbiased test set

**Threshold Study**:
An evaluation over labeled data that compares Decision Thresholds using observed TP, FP, FN, precision, recall, F1, and related metrics. It cannot be performed on an unlabeled Source Dataset.
_Avoid_: Threshold guess, final-data optimization

**Target-Prevalence Study**:
A pre-release Threshold Study that reweights or resamples labeled out-of-fold predictions to an expected class distribution, such as the organizer's approximate Benign-heavy final ratio. It estimates threshold behavior only under the assumption that class-conditional model behavior transfers to the new data; it does not reveal the true best threshold for an unlabeled final set.
_Avoid_: Benign-heavy threshold optimization, final threshold discovery

**Unlabeled Prediction Set**:
A Source Dataset without ground-truth labels, including the TEKNOFEST final test data. It supports prediction and score-distribution investigation but cannot produce observed F1, precision, recall, FP, or FN.
_Avoid_: Test set with unknown score, evaluation set

**Ground-Truth Authorization**:
The operator's explicit confirmation of which Source Dataset column contains reference labels and how its values map to Pathogenic and Benign before Evaluation is enabled.
_Avoid_: Automatic label detection, inferred labels, label-column guess

**Dataset Profile**:
The pre-prediction descriptive surface for examining Source Dataset dimensions, class composition, group composition, label coverage, and the exact source records behind a selected class or group. It may describe authorized labels but never claims model performance.
_Avoid_: Evaluation dashboard, class-performance page, automatic label summary

**Evaluated Cohort**:
The exact subset of Variant Records with authorized, valid ground-truth labels used to calculate observed performance metrics.
_Avoid_: Whole dataset, labeled-looking rows, test population

**Evaluation Workspace**:
The label-dependent surface that calculates observed F1 and supporting metrics for one Prediction Run using an authorized Ground Truth and a disclosed Evaluated Cohort.
_Avoid_: Competition scoring page, metrics dashboard, validation evidence

**Source Dataset**:
The exact CSV selected by an operator before validation, normalization, or prediction.
_Avoid_: Uploaded data, input stuff, test file

**Model Feature**:
A column required by the Inference Contract and consumed by the Production Model during prediction.
_Avoid_: Any CSV column, visible field

**Required Model Feature**:
A Model Feature whose column must exist in the Source Dataset for a Verified Run to proceed.
_Avoid_: Mandatory value, non-null feature

**Omissible Model Feature**:
A Model Feature whose absent column may be represented by the Inference Contract's declared missing value, with visible disclosure and operator confirmation.
_Avoid_: Optional prediction feature, silently filled column

**Context Column**:
A column retained from the Source Dataset for identification or investigation but not consumed by the Production Model. Its presence must not change model output.
_Avoid_: Extra feature, ignored data, unused junk

**Source Evidence**:
The identity and faithful representation of a Source Dataset, including its filename, checksum, dimensions, columns, and inspectable raw values.
_Avoid_: Upload summary, file preview

**Source Review**:
The required point in the workflow where an operator verifies Source Evidence and validation findings before explicitly authorizing prediction.
_Avoid_: Upload page, preview page

**Transformation Audit**:
The traceable account of how Source Dataset values are aligned, mapped, defaulted, or preserved as missing for each component model before inference.
_Avoid_: Hidden preprocessing, cleaned-data summary

**Model Input Evidence**:
An on-demand comparison between an original source value and the corresponding representation supplied to CatBoost or LightGBM. It is supporting evidence, not a second replacement dataset.
_Avoid_: Processed CSV, corrected source

**Prediction Run**:
One traceable execution connecting a Source Dataset, one fixed Model Package and Inference Contract, and a Result Set.
_Avoid_: Session, test, job

**Run Archive**:
The local durable collection of completed Prediction Runs, including their results, model identity, validation evidence, checksums, and Transformation Audit. It includes a Source Snapshot only with explicit operator consent.
_Avoid_: Recent files, app history, cloud history

**Source Snapshot**:
An optional local copy of the complete Source Dataset stored with an archived run for self-contained reproducibility.
_Avoid_: Automatic backup, cached upload

**Verified Run**:
An immutable Prediction Run produced with the Production Model's approved Inference Contract, including its locked decision threshold. It is the only source for official predictions and Competition Export.
_Avoid_: Default run, original run

**Result Set**:
The ordered predictions and supporting evidence produced by one Prediction Run.
_Avoid_: Dashboard, report output

**Run Summary**:
The compact status-and-orientation band above a Result Set, presenting run completion and only the few cohort facts needed before reading the table.
_Avoid_: KPI dashboard, metric-card grid, analytics header

**Ensemble Score Distribution**:
The primary cohort visualization showing how Variant Records are distributed across Ensemble Scores, with the applicable Decision Threshold marked and score-range selection linked to the results table.
_Avoid_: Confidence chart, class-performance chart, probability proof

**Component Agreement Plot**:
A cohort visualization comparing CatBoost and LightGBM scores for the same Variant Records so agreement, disagreement, and outlying model behavior can be investigated.
_Avoid_: Model accuracy plot, correlation proof, ensemble explanation

**Source Row**:
The stable positional identity of one record in the Source Dataset. It remains unchanged by sorting, filtering, investigation, or export so every prediction can be traced back to the exact source record.
_Avoid_: Table row, display index

**Record Identifier**:
The operator-visible identifier taken from `Variant_ID`, another explicitly mapped Context Column, or a generated `ROW-000001`-style value. It aids navigation but never replaces Source Row identity or satisfies an external export requirement unless that schema explicitly allows it.
_Avoid_: Primary key, guaranteed variant ID, source-row number

**Variant Record**:
The traceable view of one source row together with its final prediction, probabilities, model agreement, validation findings, and available metadata.
_Avoid_: Result row, sample

**Variant Inspector**:
The resizable detail surface that opens beside the cohort table for the selected Variant Record. It preserves cohort context and may expand when deeper investigation is needed.
_Avoid_: Detail page, result popup, modal

**Model Contribution**:
An on-demand attribution showing how a feature influenced one component model's output for a Variant Record. CatBoost and LightGBM contributions remain separate and must not be described as biological causes or clinical evidence.
_Avoid_: Biological explanation, causal feature, diagnosis reason

**AI Investigation Assistant**:
A read-only optional assistant that helps users query, summarize, and navigate application evidence. It is not part of the Production Model or Inference Contract and can propose but never execute changes to application state, verified predictions, thresholds, or exports.
_Avoid_: AI predictor, clinical assistant, model controller

**Investigation Workspace**:
The post-prediction environment for studying a Result Set, moving between cohort-level patterns and individual Variant Records without changing the Production Model.
_Avoid_: Results dashboard, analytics page

**Analysis Sandbox**:
An explicitly exploratory workspace derived from a Verified Run where users may compare alternative decision thresholds and resulting classifications without changing the Verified Run or its exports. For an Unlabeled Prediction Set it cannot claim which threshold is best or display label-dependent performance metrics.
_Avoid_: Test mode, editable results, unofficial run

**Competition Export**:
The minimal ordered prediction file produced for organizer scoring.
_Avoid_: Detailed results, analysis export

**Competition Submission Workspace**:
The competition-facing surface that validates an unlabeled Verified Run against the applicable Competition Export Profile and produces the Competition Export for external Organizer Scoring.
_Avoid_: Evaluation Workspace, final metrics page, submission dashboard

**Competition Export Profile**:
The versioned organizer-provided definition of required output columns, names, order, identifier rules, label encoding, filename, and other submission constraints used to validate a Competition Export.
_Avoid_: Guessed CSV format, model configuration, Research Export settings

**Organizer Scoring**:
The external comparison performed by the competition organizer between a team's Competition Export and private Ground Truth to calculate official F1 and any supplementary metrics.
_Avoid_: In-app final evaluation, local F1, estimated competition score

**Research Export**:
A traceable detailed output that preserves every original Source Dataset column alongside run identity and prediction evidence. It is not the organizer submission file.
_Avoid_: Competition Export, full submission

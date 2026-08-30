# Resolved Layers

**Resolved Layers** is Computational Health Lab's evidence-first desktop product for traceable model inference. Its current `Variant Inference` workflow focuses on missense-variant prediction. The present vertical slices implement Source Review, pre-prediction Dataset Profile, trusted deterministic CatBoost–LightGBM inference, immutable local Verified Runs, and a read-only post-prediction Results workspace with record-level inspection in PySide6 and Qt Quick.

## What works now

- Compact local CSV selection and a faithful, read-only Source Dataset preview.
- Virtualized QML `TableView` delegates backed by a disk-based row store and bounded 1,024-row Python cache, tested with 10,000 rows.
- A Dataset Profile available immediately after opening a CSV, with dimensions, source missingness, selectable categorical grouping, and exact raw-record drill-down before prediction.
- Explicit Ground-Truth Authorization for descriptive class composition: the operator selects a label column and maps distinct source values to Pathogenic and Benign. Missing and unrecognized values remain visible and no label-like column is interpreted automatically.
- One restrained Pathogenic/Benign composition bar, exact class coverage, compact group counts/percentages, and visible removable class/group filters that preserve immutable Source Row identity.
- SQLite-backed aggregation and filtering for the Dataset Profile, including a synthetic 10,000-row verification that does not hydrate the bounded row-page cache.
- Source Identity evidence: filename, dimensions, SHA-256, delimiter, encoding, and last-modified time.
- Integrity-checked JSON Model Package manifest loading. Loose pickle files are never accepted by the application boundary.
- Inference Contract Fit with distinct Required, Omissible, and surplus-column policy; blockers and warnings remain separate.
- Transformation Audit summaries for type handling, missing values, fixed category mappings, column alignment, and row filtering.
- Mandatory explicit operator confirmation. Changing the source resets confirmation; blocking findings keep the run action disabled.
- Deterministic, label-excluding CatBoost–LightGBM inference through an explicitly trusted, integrity-checked Model Package. The external restricted PDR package reproduces all 736 saved ensemble and component probabilities after four-decimal rounding and the expected TN 109 / FP 80 / FN 27 / TP 520 confusion matrix at threshold 0.61.
- An atomic local Run Archive that stores ordered prediction evidence plus package, contract, source, output-checksum, warning, audit, and timing evidence. It records the source path and checksum by default and never copies the Source Dataset without a future explicit opt-in flow.
- Run Archive reopening with prediction-evidence checksum verification, a compact score-distribution Overview, truthful run-level warning evidence, purposeful investigation sets, and a separate searchable Records table that retains exact Source Row identity.
- A table-visible, resizable Variant Inspector with complete prediction, component-score, threshold, run, package, contract, and source-reference evidence. It recovers the complete original row only while the archived external source remains checksum-valid and reports modified or missing sources without exposing stale values.
- The approved Split Evidence Desk hybrid v2 shell and the full-color Resolved Layers identity, currently shown from the approved raster reference without vector reinterpretation.

With an explicitly trusted manifest checksum configured, the run button creates and persists a Verified Run after Source Review confirmation, then opens its read-only Results workspace. Dataset Profile remains descriptive and never calculates F1 or other performance metrics. Evaluation, Competition Export Profiles, and read-only AI integration remain separate later workspaces.

## Setup

Python 3.10 or newer is required.

```bash
cd resolved-layers
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

On Windows, use `.venv\Scripts\python` in the equivalent commands.

## Run

Start the shell without a package:

```bash
.venv/bin/variant-inference
```

Open a Source Dataset against a validated package manifest:

```bash
.venv/bin/variant-inference \
  --model-package /absolute/path/to/package/manifest.json \
  --open /absolute/path/to/source.csv
```

Creating a Verified Run additionally requires the expected manifest SHA-256 as an independent trust anchor. The Run Archive defaults to the platform's local application-data directory:

```bash
.venv/bin/variant-inference \
  --model-package /absolute/path/to/package/manifest.json \
  --trusted-manifest-sha256 EXPECTED_SHA256 \
  --run-archive /absolute/path/to/local/run-archive \
  --open /absolute/path/to/source.csv
```

`CHL_MODEL_PACKAGE_MANIFEST`, `CHL_TRUSTED_MODEL_PACKAGE_SHA256`, and `CHL_RUN_ARCHIVE` provide equivalent local configuration. Keep machine-specific paths and restricted package material out of committed defaults. The application validates all declared artifact checksums before exposing contract policy and requires the independent manifest checksum before model deserialization.

Reopen a saved run directly from the configured archive:

```bash
.venv/bin/variant-inference \
  --run-archive /absolute/path/to/local/run-archive \
  --open-run RUN_ID
```

A clearly synthetic fixture is included only for exercising Source Review; it contains no organizer rows, mappings, or trained weights:

```bash
.venv/bin/variant-inference \
  --model-package tests/fixtures/development-package/manifest.json \
  --open tests/fixtures/source_review.csv
```

## Test and smoke check

Some ROS-enabled Linux environments globally register unrelated pytest plugins. Disabling auto-loading keeps this repository's test run isolated:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest
QT_QPA_PLATFORM=offscreen .venv/bin/variant-inference --smoke
```

For a rendered headless check:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/variant-inference \
  --model-package tests/fixtures/development-package/manifest.json \
  --open tests/fixtures/source_review.csv \
  --screenshot /tmp/chl-source-review.png
```

## Architecture

```text
src/variant_inference/
├── domain/          immutable product language and validation policy
├── application/     product use cases and typed capability ports
├── infrastructure/  CSV and validated Model Package adapters
├── qt/              thin PySide6 presentation adapters
└── qml/             custom Qt Quick application interface
```

The important boundary is intentional: CSV parsing, model-package validation, deterministic inference, Run Archive persistence, evaluation, Competition Export Profiles, and future read-only investigation evidence each have a separate port or adapter. QML does not parse data, infer schema policy, deserialize models, calculate metrics, or write exports.

## Safety and artifact policy

- Do not commit organizer data, trained weights, or category mappings derived from restricted data.
- The Production Model remains the current CatBoost–LightGBM release, but it becomes runnable only as a validated immutable Model Package with a complete Inference Contract.
- Required versus Omissible feature status must be declared by that contract. It is never inferred from an incoming final CSV.
- Source Row identity and original order are immutable.
- Evaluation and Competition Submission are separate future workspaces. Unlabeled competition data never produce local F1.
- Until the official organizer schema is published, Competition Submission must report `Organizer format pending` and cannot label an invented format as official.

Read [docs/PROJECT_MEMORY.md](docs/PROJECT_MEMORY.md), [CONTEXT.md](CONTEXT.md), and [docs/PRD.md](docs/PRD.md) before extending the product.

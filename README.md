# Resolved Layers

**Resolved Layers** is Computational Health Lab's evidence-first desktop product for traceable model inference. Its current `Variant Inference` workflow focuses on missense-variant prediction. The present vertical slices implement the approved Source Review and pre-prediction Dataset Profile workflows in PySide6 and Qt Quick; deterministic Production Model execution is deliberately the next integration milestone.

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
- The approved Split Evidence Desk hybrid v2 shell and the full-color Resolved Layers identity, currently shown from the approved raster reference without vector reinterpretation.

The run button records the completed Source Review gate but does not execute model inference yet. Dataset Profile is descriptive and never calculates F1 or other performance metrics. Run Archive persistence, Evaluation, Competition Export Profiles, and read-only AI integration are represented by separate application ports and are not implemented as UI logic.

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

`CHL_MODEL_PACKAGE_MANIFEST` may provide the manifest path for a local development machine. Keep that path out of committed defaults. The application validates all declared artifact checksums before exposing contract policy.

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
├── application/     Source Review use case and typed capability ports
├── infrastructure/  CSV and validated Model Package adapters
├── qt/              thin PySide6 presentation adapters
└── qml/             custom Qt Quick Source Review interface
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

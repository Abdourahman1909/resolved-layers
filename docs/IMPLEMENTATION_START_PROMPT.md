# Implementation Start Assignment

Recommended Codex configuration:

- Model: `gpt-5.6-sol`
- Reasoning level: `high`
- Task title: `Build Variant Inference Foundation`

## Assignment prompt

Begin implementation of the standalone Computational Health Lab Variant Inference desktop application.

### Repository boundary

- Work only inside the `variant-inference-app` repository root.
- Treat the parent repository as read-only evidence. Do not modify its Streamlit app, training code, datasets, reports, or model artifacts.
- Do not commit or push unless the user explicitly asks.

### Mandatory context before implementation

1. Read `variant-inference-app/AGENTS.md` completely.
2. Read `variant-inference-app/docs/PROJECT_MEMORY.md`, `CONTEXT.md`, `PRODUCT.md`, `docs/PRD.md`, and the relevant `docs/adr/*.md` files completely.
3. Read the parent `docs/PROJECT_MEMORY.md`.
4. Inspect only the parent inference/model files needed to understand the real saved inference contract, primarily `backend_predict.py`, the relevant configuration metadata, and narrowly relevant parts of `training_lab.py`. Do not scan the entire parent repository or load large datasets unless focused verification requires it.
5. Inspect these approved visual references:
   - `.impeccable/mocks/app/source-review-split-hybrid-v2.png` — approved Source Review.
   - `.impeccable/mocks/identity/resolved-layers.png` — locked identity.
   - `.impeccable/mocks/app/cohort-overview-v1.png` only for shell continuity; its navigation requires revision and it is not approved for implementation.

### First milestone

Build a runnable, testable vertical slice of the desktop foundation and approved Source Review workflow using PySide6 with custom QML/Qt Quick and an in-process Python core.

The milestone should include:

- A clean project/package structure and reproducible local development entry point.
- A professional, light-first application shell that faithfully follows Split Evidence Desk hybrid v2 and uses the approved full-color Resolved Layers identity without redesigning it.
- A compact `Open CSV` action—no large generic upload/drop page.
- Read-only source preview with scalable table behavior suitable for up to 10,000 rows; do not eagerly create thousands of QML objects.
- Source Identity evidence: file name, rows/columns, SHA-256, delimiter, encoding, and last-modified time.
- Inference Contract Fit architecture and UI: required, omissible, and surplus columns; blocking issues; and warnings. Do not improvise feature policy from final data.
- Transformation Audit architecture and UI: type handling, missing-value behavior, category mapping, row filtering, and an audit-log entry point.
- Explicit operator checkbox confirmation before the run action can be enabled.
- Clear domain, application, and infrastructure boundaries so CSV parsing, model-package validation, deterministic inference, run archive, evaluation, competition export profiles, and a future read-only AI integration are separate adapters/services rather than UI logic.
- Tests for the non-visual core behavior implemented in this milestone, including CSV identity/checksum, schema compatibility, and confirmation gating where practical.
- A concise README section with setup, run, and test commands.

### Important boundaries

- The current CatBoost–LightGBM release is the only first-release Production Model. Design around a validated immutable Model Package and Inference Contract, not arbitrary model uploads.
- Do not copy or commit organizer data, trained weights, category mappings derived from restricted data, or organizer example rows. If actual artifacts are needed during local development, reference them read-only and keep that path/configuration out of committed defaults.
- Do not invent the organizer's unknown final submission schema. Competition Export must remain behind a versioned Competition Export Profile and show `Organizer format pending` until official instructions arrive.
- Do not calculate or display F1 for unlabeled competition data. Evaluation and Competition Submission are separate future workspaces.
- Do not implement the unresolved post-prediction navigation or treat `cohort-overview-v1` as approved.
- Do not add training, Optuna, ablation, arbitrary threshold switching, generic model upload, or AI/internet features.
- Preserve immutable Source Row identity and official export order.
- Avoid default Qt styling, KPI-card dashboards, decorative charts, gradients, excessive shadows, and generic AI-dashboard patterns.
- Use the approved raster identity as a reference or temporary asset if needed; do not reinterpret or replace the logo. Production vectorization remains a separate unresolved task.

### Execution expectations

- Explain the implementation plan briefly, then proceed autonomously with safe local edits and validation.
- Make reasonable implementation decisions within this milestone. Ask only if a missing choice would materially change the product contract.
- Keep progress updates concise.
- At completion, run relevant tests and a startup/smoke check, report exact results, and update `variant-inference-app/docs/PROJECT_MEMORY.md` under **Where work stopped** with what was actually completed, remaining limitations, and the next practical step.

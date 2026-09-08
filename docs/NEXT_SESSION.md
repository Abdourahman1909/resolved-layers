# Next session

> Written 2026-09-09. Kept in the repository deliberately: the previous handoff
> was written to `/tmp` and was lost when the machine cleared it.

Read `AGENTS.md`, then `docs/PROJECT_MEMORY.md` in full — especially **6a.
Immediate next step**. This file only orients you; the memory is authoritative.

## Where things stand

`main` is clean, all work merged, no open pull requests, **172 tests passing**.
Two releases are published: **v0.1.0** and **v0.2.0**.

The application does the whole competition workflow offline from a single
AppImage: install a Model Package from Settings, open a CSV, review it, run
deterministic inference, investigate per panel, evaluate against authorized
labels, and write the official submission JSON.

## The one deadline

**TEKNOFEST final: 16–18 September 2026, Dicle University.** University and
Above runs the afternoon of the 16th; all teams must be present by 09:30.
Internet access is forbidden during the test, which is why the self-contained
AppImage matters. The submission format is fixed and implemented; see
`TEKNOFEST_2026_Saglikta_Yapay_Zeka_Final_Uygulama_ve_Sonuc_Teslim_Kilavuzu.pdf`
in this repository.

## What to do first

1. **Build the second Model Package at threshold 0.75**, beside the untouched
   0.61 one. This was agreed and not started. Memory section 6a has the detail,
   including that the manifest checksum changes and must be pinned.
2. **Release 0.2.1.** The AppImage installed at `~/Applications/` is 0.2.0 and
   lacks four interface fixes made after it was built.

Both are bounded. Neither is blocked.

## The open question that decides the threshold

**Is the final test set class-balanced, as the specification describes?**

The specification states balanced test sets (1000/1000, 100/100, 100/100,
30/30), but the delivered training data is 74% Pathogenic. They disagree.

- Balanced → adopt **0.75**, worth roughly +0.022 on the final metric
- Skewed like the delivered data → **0.61** is already right

The user was going to ask the organisers. Ask whether they did before assuming
either. The full analysis is in the parent repository at
`results/rebalance_experiment_2026-09-04/`.

## How this project is worked on

Focused `codex/...` branches, one bounded milestone at a time, a pull request
per milestone, and `docs/PROJECT_MEMORY.md` updated when state or a durable
decision changes. Explain a plan before substantial work. Do not commit
organizer data, trained weights, derived mappings, or machine-specific paths;
the Model Package lives outside this repository for that reason.

## Something worth knowing before you trust the test suite

Four real defects were found in one evening by the user simply using the
application, and **none was visible to the 172 tests**: prediction froze the
interface and produced duplicate runs from repeated clicks, nothing could be
grabbed to scroll, the submission surface showed a stale warning beside an
enabled button, and the archive delete control never received its clicks.

The suite verifies controllers and that surfaces render. It does not verify that
a control receives the click aimed at it. Driving real clicks was attempted and
abandoned — an offscreen `Popup` does not instantiate its delegates here — and
that limit is recorded in `tests/test_archive_delete_ui.py`.

So: after changing anything interactive, **run the application and use it**.
`.venv/bin/python -m variant_inference`. A passing suite is not evidence that a
button works.

Two related traps, both of which produced a wrong conclusion here before being
caught: a cross-thread test passed only because the main thread had already
cached the row the worker read, and the offscreen smoke check cannot see faults
in the archive row because it starts with an empty archive.

## Practical notes

- The project path contains spaces, so PyInstaller cannot build in place;
  `packaging/build-standalone.sh` stages a space-free copy.
- `appimagetool` is at `~/.local/share/resolved-layers-build/appimagetool.AppImage`.
  Pass it as `APPIMAGE_TOOL=...`; it was previously kept in `/tmp` and lost.
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest`
- The user's Model Package is configured through
  `~/.config/environment.d/resolved-layers.conf`, so a menu launch finds it.
- Restricted artifacts live in the parent repository at
  `results/production_model_packages/teknofest-2026-pdr-v1/`.

## Model questions

Questions about how the model was trained belong in the **parent** repository,
which has its own orientation file at `docs/CONTEXT_FOR_NEW_CHAT.md`. Note the
warning recorded there: `docs/HOW_THE_MODEL_WORKS.md` describes a three-model
ensemble, which is **not** what ships. Both the submitted report and the released
package describe two members, CatBoost and LightGBM.

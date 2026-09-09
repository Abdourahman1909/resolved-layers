# Next session

> Written 2026-09-09. Kept in the repository deliberately: an earlier handoff
> was written to `/tmp` and was lost when the machine cleared it.

Read `AGENTS.md`, then `docs/PROJECT_MEMORY.md` in full — especially **6a.
Immediate next step**. This file only orients you; the memory is authoritative.

## Where things stand

`main` is clean, all work merged, **187 tests passing**. Three releases are
published: **v0.1.0**, **v0.2.0** and **v0.2.1**.

The application does the whole competition workflow offline from a single
AppImage: install a Model Package from Settings, open a CSV, review it, run
deterministic inference, investigate per panel, evaluate against authorized
labels, and write the official submission JSON.

Both agreed items from the previous handoff are done. The two Model Packages
exist and are pinned, and 0.2.1 is released and installed.

## The one deadline

**TEKNOFEST final: 16–18 September 2026, Dicle University.** University and
Above runs the afternoon of the 16th; all teams must be present by 09:30.
Internet access is forbidden during the test, which is why the self-contained
AppImage matters. The submission format is fixed and implemented; see
`TEKNOFEST_2026_Saglikta_Yapay_Zeka_Final_Uygulama_ve_Sonuc_Teslim_Kilavuzu.pdf`
in this repository.

## The one question that still decides something

**Is the final test set class-balanced, as the specification describes?**

The specification states balanced test sets (1000/1000, 100/100, 100/100,
30/30), but the delivered training data is 74% Pathogenic. They disagree.

- Balanced → install the **0.75** package, worth roughly +0.022 on the metric
- Skewed like the delivered data → install the **0.61** package

Both packages are built, verified, and pinned, so this is now a choice made on
the day rather than work to do. The user had not heard back from the organisers
as of 2026-09-09. The full analysis is in the parent repository at
`results/rebalance_experiment_2026-09-04/`.

Concrete numbers, measured in the application on the 736-row held-out file,
which follows the **delivered** distribution rather than the specification:

| Threshold | Pathogenic | mean F1 | mean MCC |
| --- | --- | --- | --- |
| 0.61 | 600 | 0.9306 | 0.5552 |
| 0.75 | 551 | 0.8916 | 0.4639 |

So on delivery-shaped data 0.61 wins clearly. That is the predicted behaviour,
not a refutation of 0.75 — the case for 0.75 is built on the specification's
balanced composition. Do not quote the table above as evidence against 0.75
without saying which distribution it came from.

## The two Model Packages

Both live outside this repository, in the ignored parent path
`results/production_model_packages/`:

- `teknofest-2026-pdr-v1` — threshold 0.61, untouched, manifest
  `fc20e611…8d923d`
- `teknofest-2026-pdr-v1-threshold-075` — threshold 0.75, manifest
  `b5c8f2e7…82e40f2`

Both checksums are pinned in `OFFICIAL_MANIFEST_CHECKSUMS`, so either installs
from Settings with no trust prompt. They hold byte-identical artifacts and were
verified to produce identical scores, differing only in classification and only
for scores inside `[0.61, 0.75)`. Re-check that at any time with:

```bash
.venv/bin/python scripts/compare_threshold_packages.py --package A --package B --source CSV
```

## Before the day: one machine configuration change

`~/.config/environment.d/resolved-layers.conf` pins
`CHL_MODEL_PACKAGE_MANIFEST` to the 0.61 package, and that variable takes
priority over whatever Settings installs. The application now says so plainly —
Settings names the variable and the package it supplied — rather than silently
disagreeing with itself. But the cleanest setup is to **delete that file**,
since both checksums are pinned and its `CHL_TRUSTED_MODEL_PACKAGE_SHA256` is no
longer needed either. Settings then becomes the single place the package is
chosen, which is what you want when the choice is made under time pressure. It
takes effect at the next login.

## Something worth knowing before you trust the test suite

Four real defects were found in one evening by the user simply using the
application, and none was visible to the 172 tests at the time: prediction froze
the interface and produced duplicate runs from repeated clicks, nothing could be
grabbed to scroll, the submission surface showed a stale warning beside an
enabled button, and the archive delete control never received its clicks.

Three more were found the same way on 2026-09-09, all in the Settings surface:
it reported the installed Model Package as ready while a different one was
actually predicting; the first fix for that printed the same sentence twice; and
it still said "No Model Package installed" on a machine where the environment
variable was the only route a package arrived by, while prediction worked.

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

- Driving the interface by hand works: X11 with `xdotool`, `wmctrl` and
  `import`. The GTK portal file dialog ignores synthetic typing; put the path on
  the clipboard with `xclip` and paste it into the Ctrl+L location bar instead.
- The project path contains spaces, so PyInstaller cannot build in place;
  `packaging/build-standalone.sh` stages a space-free copy.
- `appimagetool` is at `~/.local/share/resolved-layers-build/appimagetool.AppImage`.
  Pass it as `APPIMAGE_TOOL=...`; it was previously kept in `/tmp` and lost.
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest`
- Restricted artifacts live in the parent repository at
  `results/production_model_packages/`.

## Model questions

Questions about how the model was trained belong in the **parent** repository,
which has its own orientation file at `docs/CONTEXT_FOR_NEW_CHAT.md`. Note the
warning recorded there: `docs/HOW_THE_MODEL_WORKS.md` describes a three-model
ensemble, which is **not** what ships. Both the submitted report and the released
package describe two members, CatBoost and LightGBM.

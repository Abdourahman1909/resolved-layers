# Next session

> Written 2026-09-09. Kept in the repository deliberately: an earlier handoff
> was written to `/tmp` and was lost when the machine cleared it.

Read `AGENTS.md`, then `docs/PROJECT_MEMORY.md` in full — especially **6a.
Immediate next step**. This file only orients you; the memory is authoritative.

## Where things stand

`main` is clean, **197 tests passing**, everything merged and published. Three
releases: **v0.1.0**, **v0.2.0** and **v0.2.1**. The v0.2.1 release carries both
a Linux AppImage and a Windows zip.

The 0.2.1 AppImage is installed at `~/Applications/` and registered in the
applications menu; 0.2.0 and 0.1.0 are archived in `previous-versions/`.

The application does the whole competition workflow offline from a single
build: install a Model Package from Settings, open a CSV, review it, run
deterministic inference, investigate per panel, evaluate against authorized
labels, and write the official submission JSON.

Both agreed items from the previous handoff are done, and a Windows build was
added afterwards.

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
as of 2026-09-09.

**The loss is asymmetric, and it favours 0.75.** `threshold_regret.py` in the
parent repository at `results/rebalance_experiment_2026-09-04/` reuses that
experiment's out-of-fold scores and varies only the assumed class composition:

| Hypothesis | 0.61 | 0.75 |
| --- | --- | --- |
| Balanced 50/50, as specified | 0.7407 | **0.7615** |
| Delivered, one 74% share | **0.7980** | 0.7915 |
| Delivered, each panel's own share | **0.7986** | 0.7873 |

Picking 0.61 and being wrong costs 0.0207. Picking 0.75 and being wrong costs
0.0065 to 0.0113. **0.75 has the smaller worst case under both readings**, so it
is the better default even without an answer from the organisers.

Do **not** judge this from the 736-row held-out file. Measured there, 0.61 looks
better by about 0.065 (mean F1 0.9306 / MCC 0.5552 against 0.8916 / 0.4639) — but
that split leaves PAH and CFTR with two observed negatives each, and per-panel
MCC on two negatives is noise. The out-of-fold design exists precisely because
the single split cannot support per-panel estimates. That trap was walked into
once on 2026-09-09 and corrected.

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

## Which Model Package a launch uses

Order, decided by `resolve_model_package` in `main.py` and pinned by tests:

1. `--model-package` — a deliberate instruction for one launch
2. **the package installed through Settings**
3. `CHL_MODEL_PACKAGE_MANIFEST` — a fallback only when nothing is installed

The variable used to sit at position 2 and beat Settings. It predates in-app
installation, when it was the only way a menu launch could find a package at
all, and it kept its priority after Settings was built. That is how an operator
installed the 0.75 package, pressed Install, ran a prediction, and got 0.61: the
choice was stored correctly and never consulted. Flipped on 2026-09-09 at the
user's instruction.

`~/.config/environment.d/resolved-layers.conf` was also deleted that day. Note
that deleting it does not clear a running session: systemd reads `environment.d`
once at login, and `gnome-shell` keeps its own copy for the life of the session,
so every menu launch inherits it until the next login. That no longer matters
for correctness — Settings wins either way — but it is why the variable can
still appear to be set long after the file is gone.

## Something worth knowing before you trust the test suite

Four real defects were found in one evening by the user simply using the
application, and none was visible to the 172 tests at the time: prediction froze
the interface and produced duplicate runs from repeated clicks, nothing could be
grabbed to scroll, the submission surface showed a stale warning beside an
enabled button, and the archive delete control never received its clicks.

Four more were found the same way on 2026-09-09. Three were in Settings: it
reported the installed Model Package as ready while a different one was actually
predicting; the first fix for that printed the same sentence twice; and it still
said "No Model Package installed" where the environment variable was the only
route a package arrived by, while prediction worked.

The fourth is the one to remember. The user installed the 0.75 package, ran a
prediction, and got 0.61. The code was correct and Settings had said so — but the
warning lived only in Settings, which nobody revisits after installing, so it
arrived after the run instead of before it. Source Review now shows the Release
Threshold and names the route the package came from. **A warning belongs where
the decision is taken, not where the setting was made.**

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

## Deferred on purpose

A Turkish/English interface switch was raised on 2026-09-09 and deliberately put
off until after the final: about 350 unmarked strings across every surface, and
the hard part is authoring a locked Turkish counterpart to the `CONTEXT.md`
glossary rather than the mechanics. Section 5 of the memory records the full
assessment so it does not have to be worked out again. Nothing in the competition
guide requires a Turkish interface.

## The Windows build has never been used by a person

`.github/workflows/windows-build.yml` builds it on a `windows-latest` runner and
proves it can predict, by running real inference against a synthetic package
`scripts/make_smoke_package.py` assembles from two tiny boosters. The first run
produced predictions bit-identical to Linux, to twelve decimals.

What no runner can do is click. **Nobody has opened the Windows build and used
it**, and every interface defect in this project was found exactly that way. Do
not trust it for anything that matters until someone has.

Run it without publishing a release:

```bash
gh workflow run "Windows build" --ref main
```

## Model questions

Questions about how the model was trained belong in the **parent** repository,
which has its own orientation file at `docs/CONTEXT_FOR_NEW_CHAT.md`. Note the
warning recorded there: `docs/HOW_THE_MODEL_WORKS.md` describes a three-model
ensemble, which is **not** what ships. Both the submitted report and the released
package describe two members, CatBoost and LightGBM.

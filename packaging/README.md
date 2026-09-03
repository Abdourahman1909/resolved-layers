# Packaging Resolved Layers for Linux

This directory builds and installs the distributable Linux desktop application.
It produces a build that another person can install and open on their own
machine without a development checkout.

## What a build contains

The build carries the application, its QML surfaces, and the shipped
Computational Health Lab identity assets.

It deliberately **does not** carry a Model Package, trained weights, an Inference
Contract, organizer data, or any machine-specific path. Those remain restricted
artifacts supplied separately and only when authorized.

## Behaviour without a Model Package

An installed build with no Model Package stays fully usable for everything that
does not require the Production Model:

- Source Review, including Source Identity evidence and the raw source table
- Dataset Profile, including grouping, missingness, and authorized label mapping
- Opening and inspecting Verified Runs already present in the local Run Archive
- Records, the Variant Inspector, and Evaluation for those archived runs

Prediction is unavailable and reports `No Model Package installed`. It does not
report a fabricated fault, and it does not blame the reviewed Source Dataset for
blocking issues that dataset does not have.

Supply a package at launch once it is authorized:

```
resolved-layers --model-package /path/to/MANIFEST.json \
                --trusted-manifest-sha256 <sha256>
```

## Build

```
packaging/build-linux.sh
```

This regenerates the identity assets from the locked reference sheet when
Pillow is available, verifies the shipped assets are present, and writes a wheel
to `dist/`.

## Install

```
packaging/install-linux.sh dist/chl_resolved_layers-*.whl
```

The installer needs no administrator rights. It creates an isolated runtime
under `~/.local/opt/resolved-layers`, links the launcher into `~/.local/bin`,
installs the application icons into the user's `hicolor` icon theme, and
registers the desktop entry so the application appears in the applications menu.

Override the destination with `PREFIX=/some/prefix`.

## Uninstall

```
packaging/uninstall-linux.sh
```

This removes the runtime, launcher, icons, and desktop entry. It leaves the
local Run Archive untouched, so persisted Verified Runs survive an uninstall and
must be removed deliberately.

## Identity assets

`scripts/extract_identity_assets.py` cuts the shipped symbol, horizontal lockup,
and application icons out of the locked identity reference at
`.impeccable/mocks/identity/resolved-layers.png`.

It does not design, redraw, or reinterpret the identity. Regenerating from an
unchanged reference reproduces the same assets. Production vectorization of the
approved mark remains separate, unresolved work; the shipped raster icons are
sufficient for desktop use.

## Known limits

- The build targets Linux. A Windows build is later bounded work; the icon
  extraction already emits the required `.ico`.
- The runtime installs CatBoost, LightGBM, scikit-learn, pandas, and NumPy
  because the inference core imports them at startup. The isolated runtime is
  therefore large even though no model ships with it.
- The build is a wheel installed into an isolated interpreter, so the target
  machine needs `python3` with `venv`. A fully self-contained Nuitka build that
  removes that requirement is not yet part of this milestone.
- The full-colour icon keeps a black element that loses contrast on a dark
  desktop dock. The locked reference sheet defines a reversed treatment for that
  case; wiring it to the desktop theme is not yet done.

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

## Installing a Model Package

Open **Settings** in the application, choose the package folder, review the
identity and manifest checksum it reports, and install it. This is the route
that needs no terminal, and it is how someone who is not the developer installs
a package they received separately.

A package recognised as official loads directly. Any other package shows an
explicit trust warning and cannot be installed until the operator confirms that
exact manifest checksum, because loading a package deserializes model artifacts.
Installing records only the package location and checksum; no artifact is copied.

The command-line route remains available and takes precedence:

```
resolved-layers --model-package /path/to/MANIFEST.json \
                --trusted-manifest-sha256 <sha256>
```

Resolution order is argument, then `CHL_MODEL_PACKAGE_MANIFEST`, then the
package installed through Settings.

## Standalone build (no Python required)

```
packaging/build-standalone.sh
```

Produces `dist/Resolved_Layers-x86_64.AppImage`: one file the recipient makes
executable and opens. It bundles its own Python runtime, Qt, CatBoost, and
LightGBM, so the target machine needs none of them.

```
chmod +x Resolved_Layers-x86_64.AppImage
./Resolved_Layers-x86_64.AppImage
```

Set `BUILD_APPIMAGE=0` to produce a tarball instead, and `APPIMAGE_TOOL=/path/to/appimagetool`
if the tool is not on `PATH`. Get it from
https://github.com/AppImage/appimagetool/releases.

### Verifying a build can actually predict

A bundled build loads CatBoost and LightGBM as native libraries that no static
import names, so a broken bundle starts normally and fails only at prediction.
Check it directly:

```
./Resolved_Layers-x86_64.AppImage --verify-inference \
    --model-package /path/to/manifest.json \
    --open /path/to/source.csv
```

It reports the package, threshold, record count, class counts, and the first
row's ensemble score, then exits. Compare those against a known run.

### Why the build stages a copy

PyInstaller splits paths on whitespace when resolving shared-library
dependencies, so a build fails if the project or its environment sits under a
path containing spaces. The script stages a space-free copy and builds in a
fresh isolated environment, which also keeps the build independent of the
development checkout.

## Build the wheel

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
- Two build shapes exist. The wheel needs `python3` with `venv` on the target
  machine; the AppImage needs nothing and is the one to hand to someone else.
- The AppImage is around 300 MB compressed, roughly 900 MB extracted. Qt modules
  the application never uses are already excluded; the remainder is CatBoost, Qt,
  and the scientific stack, and cannot be reduced further without removing
  functionality.
- A build made on Ubuntu 22.04 requires glibc 2.35 or newer on the target
  machine and will not start on Ubuntu 20.04 or older. Building inside a
  container with an older base fixes this and is not yet done. AppImage does not
  solve it; it is a glibc question, not a packaging one.
- The standalone build bundles bytecode, not compiled source. Source hiding was
  considered and deliberately not required.
- The full-colour icon keeps a black element that loses contrast on a dark
  desktop dock. The locked reference sheet defines a reversed treatment for that
  case; wiring it to the desktop theme is not yet done.

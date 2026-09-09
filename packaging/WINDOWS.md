# Resolved Layers on Windows

This archive contains the application and everything it needs to run. There is
no installer and nothing is written outside the folder you unpack it into,
except the settings and Run Archive described below.

## Install it

Two downloads are published for Windows. Prefer the installer.

**`Resolved_Layers-<version>-windows-x86_64-Setup.exe`** installs the
application for your user only, so it never asks for an administrator. It adds a
Start menu shortcut with the application icon, an entry in Add or remove
programs, and an uninstaller. Installing a newer version replaces the previous
one rather than leaving two entries.

**`Resolved_Layers-<version>-windows-x86_64.zip`** is the same build as a plain
folder, for a machine where you would rather install nothing. Unpack it and run
`resolved-layers.exe` from the unpacked folder. Keep the folder together: the
executable loads Qt, CatBoost and LightGBM from the files beside it, so moving
`resolved-layers.exe` on its own will not work.

Windows SmartScreen will warn that the publisher is unrecognised, for either
download, because the build is not code-signed. Choose **More info**, then **Run
anyway**. Signing needs a purchased certificate, and this build is distributed
from the repository it is built from instead.

## It ships without a Model Package

A build carries no model weights, no Inference Contract, and no organizer data.
Prediction reports `No Model Package installed` until you install one.

Everything else works immediately: opening a CSV, Source Review, the Dataset
Profile, and any archived Verified Run including Records, the Variant Inspector
and Evaluation.

To install a package, open **Settings**, choose **Select package folder…**, and
pick the folder containing the package's `manifest.json`. The application shows
the package identity, its Release Threshold, its manifest checksum and the
number of verified artifacts before you decide. A package this release
recognises installs without a prompt; anything else must have its exact checksum
confirmed first, because model artifacts are unpickled and unpickling runs code.

**Restart the application after installing.** The package is read once at
startup. Source Review shows the Release Threshold the run will use, so you can
confirm which package is active before predicting.

## Where it keeps things

- Settings: `%APPDATA%\Computational Health Lab\Resolved Layers\model-package.json`
  — a path and confirmed checksums only, never a model artifact.
- Run Archive: `%LOCALAPPDATA%\Computational Health Lab\Resolved Layers\runs`
  — completed Verified Runs.

**Uninstalling removes neither.** A completed Verified Run is evidence, and
removing the application is not a decision to destroy it. Delete those folders
yourself if you want them gone.

Neither contains organizer data. A Verified Run records the path and checksum of
the source dataset it read, not a copy of it, unless you opt into a snapshot.

## Requirements

64-bit Windows 10 or later. Nothing else: the build carries its own Python
runtime, Qt, CatBoost and LightGBM.

## Verifying a build

The archive is produced by the `Windows build` workflow in this repository,
which builds on a clean runner, starts the application with no Model Package,
and runs real inference against a synthetic package it assembles from two tiny
boosters. That proves the bundle can load and execute its native libraries,
which a failed bundle otherwise only reveals when someone tries to predict.

The workflow cannot use the interface. Before trusting a Windows build for
anything that matters, open it and use it.

Licence and third-party notices are in `LICENSE` and `THIRD-PARTY-NOTICES.md`
beside this file.

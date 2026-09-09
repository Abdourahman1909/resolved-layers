# Resolved Layers on Windows

This archive contains the application and everything it needs to run. There is
no installer and nothing is written outside the folder you unpack it into,
except the settings and Run Archive described below.

## Run it

1. Unpack the archive somewhere you will keep it, such as your user folder.
2. Open the unpacked folder and run **`resolved-layers.exe`**.

Windows SmartScreen may warn that the publisher is unrecognised, because the
executable is not code-signed. Choose **More info**, then **Run anyway**. If you
would rather not, the Linux AppImage is signed by nothing either, and both are
built from the source in this repository.

Keep the folder together. The executable loads Qt, CatBoost and LightGBM from
the files beside it, so moving `resolved-layers.exe` on its own will not work.
To put it in the Start menu, right-click the executable and choose **Pin to
Start**.

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
  — completed Verified Runs. Deleting the application folder leaves these; remove
  them yourself if you want them gone.

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

# Third-party notices

Resolved Layers is released under the MIT License. The distributed application
bundles the third-party components below, each under its own license.

This file is a good-faith record of what a build contains, not legal advice.

## Bundled in the standalone build

| Component | Purpose | License |
| --- | --- | --- |
| [Qt](https://www.qt.io/) via [PySide6](https://doc.qt.io/qtforpython/) | Application framework and Qt Quick interface | LGPL-3.0 |
| [CatBoost](https://catboost.ai/) | Gradient-boosting inference component | Apache-2.0 |
| [LightGBM](https://lightgbm.readthedocs.io/) | Gradient-boosting inference component | MIT |
| [NumPy](https://numpy.org/) | Numerical arrays | BSD-3-Clause |
| [pandas](https://pandas.pydata.org/) | Tabular data handling | BSD-3-Clause |
| [SciPy](https://scipy.org/) | Scientific routines required by the model components | BSD-3-Clause |
| [scikit-learn](https://scikit-learn.org/) | Model interfaces required to load the saved components | BSD-3-Clause |
| [CPython](https://www.python.org/) | Bundled language runtime | PSF-2.0 |

The standalone build is assembled with [PyInstaller](https://pyinstaller.org/)
(GPL-2.0 with a bootloader exception permitting the distribution of proprietary
and differently licensed applications) and packaged with
[appimagetool](https://github.com/AppImage/appimagetool) (MIT). Neither is part
of the shipped application.

## Qt and the LGPL

Qt is used under the **LGPL-3.0**. The standalone build links it dynamically:
the Qt libraries ship as separate shared objects inside the AppImage rather than
being compiled into the executable.

Recipients therefore retain the rights the LGPL requires, including the ability
to obtain the Qt source, and to modify and replace the bundled Qt libraries.
An AppImage can be unpacked with `--appimage-extract`, its Qt shared objects
replaced, and the result run again.

Qt source is available from https://download.qt.io/. The full LGPL-3.0 text is
available at https://www.gnu.org/licenses/lgpl-3.0.html.

No GPL-only Qt module is used. The build deliberately excludes every Qt module
the application does not need, including Qt Charts, Qt Graphs, Qt Data
Visualization, Qt WebEngine, and the Qt 3D modules.

## What is not included

The distributed application contains **no Model Package**, no trained model
weights, no feature mappings, and no dataset. Those are supplied separately and
are not covered by this repository's license.

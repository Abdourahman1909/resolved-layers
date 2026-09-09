# PyInstaller specification for the standalone Resolved Layers build.
#
# Produces a self-contained directory that runs without Python installed. The
# build carries no Model Package: a package is supplied separately and installed
# from Settings, exactly as with the wheel.
#
# Build with packaging/build-standalone.sh rather than calling PyInstaller
# directly, so the identity assets are regenerated and verified first.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

PROJECT_ROOT = Path(SPECPATH).parent
PACKAGE_ROOT = PROJECT_ROOT / "src" / "variant_inference"

# QML surfaces and the shipped identity assets are read from disk at runtime,
# so they must travel with the build rather than being imported.
datas = [
    (str(PACKAGE_ROOT / "qml"), "variant_inference/qml"),
    (str(PACKAGE_ROOT / "assets"), "variant_inference/assets"),
]

# CatBoost and LightGBM load native libraries that a bytecode scan cannot see.
binaries = []
for package in ("catboost", "lightgbm"):
    binaries += collect_dynamic_libs(package)
    datas += collect_data_files(package, include_py_files=False)

# Model artifacts are unpickled at run time, so every module the pickles name
# must be importable even though nothing imports them statically.
hiddenimports = [
    "catboost",
    "lightgbm",
    "numpy",
    "pandas",
    "sklearn",
    "sklearn.ensemble",
    "sklearn.preprocessing",
    "sklearn.tree",
    "scipy.special",
    "scipy.sparse",
]

# Qt modules this application never uses. PySide6 ships every module, which is
# the single largest contributor to build size.
EXCLUDED_QT = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtNfc", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtPositioning", "PySide6.QtRemoteObjects",
    "PySide6.QtScxml", "PySide6.QtSensors", "PySide6.QtSerialBus",
    "PySide6.QtSerialPort", "PySide6.QtSpatialAudio", "PySide6.QtSql",
    "PySide6.QtStateMachine", "PySide6.QtTest", "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools", "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets", "PySide6.QtWebSockets",
    "PySide6.QtGraphs", "PySide6.QtGraphsWidgets", "PySide6.QtQuick3D",
    "PySide6.QtNetworkAuth", "PySide6.QtHttpServer",
]

# Plotting and notebook libraries reachable through CatBoost. This application
# renders every chart itself in QML and never calls them.
EXCLUDED_PLOTTING = [
    "matplotlib", "plotly", "IPython", "ipywidgets", "notebook",
    "tkinter", "PIL", "PyQt5", "PyQt6", "graphviz",
]

analysis = Analysis(
    [str(PACKAGE_ROOT / "__main__.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[*EXCLUDED_QT, *EXCLUDED_PLOTTING],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

# Windows wants an .ico and rejects a PNG here; every other target takes the
# PNG. Both ship, produced from the same locked identity reference.
ICON = PACKAGE_ROOT / "assets" / "icons" / (
    "resolved-layers.ico" if sys.platform == "win32" else "resolved-layers-256.png"
)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="resolved-layers",
    console=False,
    icon=str(ICON),
)

collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    name="resolved-layers",
)

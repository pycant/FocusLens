# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for FocusLens — AI-Powered Focus Tracking"""

import os
import sys

sys.setrecursionlimit(5000)

# SPECPATH is the directory containing this spec file (build/)
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

# Ensure PyQt6 Qt6 bin directory is in PATH to avoid DLL conflicts
_qt_bin = os.path.join(
    os.path.dirname(os.__file__), "site-packages", "PyQt6", "Qt6", "bin"
)
if os.path.isdir(_qt_bin):
    os.environ["PATH"] = _qt_bin + os.pathsep + os.environ.get("PATH", "")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "resources", "icons"), "resources/icons"),
        (os.path.join(ROOT, "resources", "sounds"), "resources/sounds"),
        (os.path.join(ROOT, "resources", "focuscam.sql"), "resources"),
        (os.path.join(ROOT, "resources", "haarcascade_frontalface_default.xml"), "resources"),
        (os.path.join(ROOT, "resources", "haarcascade_eye.xml"), "resources"),
        (os.path.join(ROOT, "config", "default_settings.json"), "config"),
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtMultimedia",
        "PyQt6.QtSvg",
        "app",
        "core",
        "config",
        "utils",
        "app.main_window",
        "app.camera_widget",
        "app.statistics_widget",
        "app.contribution_grid",
        "app.distraction_overlay",
        "app.login_dialog",
        "app.settings_dialog",
        "app.scheduler_dialog",
        "app.theme",
        "core.camera_manager",
        "core.detector",
        "core.distraction_engine",
        "config.settings",
        "utils.database",
        "utils.logger",
        "mysql.connector",
        "mediapipe",
        "cv2",
        "PIL",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6.QtBluetooth",
        "PyQt6.QtDBus",
        "PyQt6.QtNetwork",
        "PyQt6.QtNfc",
        "PyQt6.QtOpenGL",
        "PyQt6.QtOpenGLWidgets",
        "PyQt6.QtPositioning",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "PyQt6.QtQuick3D",
        "PyQt6.QtRemoteObjects",
        "PyQt6.QtSensors",
        "PyQt6.QtSerialPort",
        "PyQt6.QtSql",
        "PyQt6.QtTest",
        "PyQt6.QtTextToSpeech",
        "PyQt6.QtWebChannel",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineQuick",
        "PyQt6.QtWebSockets",
        "PyQt6.QtXml",
        "tensorflow",
        "matplotlib",
        "scipy",
        "notebook",
        "jupyter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FocusLens",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FocusLens",
)

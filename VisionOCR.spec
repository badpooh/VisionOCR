# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = os.path.abspath(SPECPATH)
scripts_dir = os.path.join(project_dir, "python_scripts")
sys.path.insert(0, scripts_dir)


def existing(path):
    full = os.path.join(project_dir, path)
    return full if os.path.exists(full) else None


datas = []

# Runtime data expected through relative paths after python_scripts/main.py
# changes cwd. Keep only data/model assets here; Python source modules are
# bundled by PyInstaller as bytecode, not copied as .py files.
for src, dest in (
    ("config", "config"),
    ("python_scripts/ppocr", "ppocr"),
    ("python_scripts/function/yolov11_model", "function/yolov11_model"),
    ("python_scripts/demo_test/image_ref", "demo_test/image_ref"),
):
    full = existing(src)
    if full:
        datas.append((full, dest))

# Package resources used by PaddleOCR/Ultralytics at runtime.
datas += collect_data_files("paddleocr")
datas += collect_data_files("ultralytics")

hiddenimports = []
for package in (
    "config",
    "demo_test",
    "device",
    "function",
    "models",
    "setup_test",
    "ui",
):
    hiddenimports += collect_submodules(package)

hiddenimports += [
    "pymodbus.client",
    "paddleocr",
    "ultralytics",
    "cv2",
]


a = Analysis(
    ["python_scripts/main.py"],
    pathex=[project_dir, scripts_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib.tests",
        "numpy.tests",
        "pandas.tests",
        "pytest",
        "tkinter",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VisionOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    name="VisionOCR",
)

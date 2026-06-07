from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path.cwd()
app_dir = project_root / "CameraTrapAssistant"
src_dir = app_dir / "src"

datas = [
    (str(app_dir / "resources"), "resources"),
    (str(src_dir / "models" / "weights"), "models/weights"),
    (str(src_dir / "models" / "model_manifest.json"), "models"),
    (str(src_dir / "models" / "LICENSE.txt"), "models"),
]
datas += collect_data_files("ultralytics")
datas += collect_data_files("tkintermapview")

hiddenimports = [
    "models.predictTools",
    "models.detectTools",
    "models.classifTools",
    "models.fileManager",
    "models.load_api_results",
]

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "tensorflow",
        "tensorboard",
        "onnx",
        "onnxruntime",
        "openvino",
        "IPython",
        "jupyter",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CameraTrapAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CameraTrapAssistant",
)

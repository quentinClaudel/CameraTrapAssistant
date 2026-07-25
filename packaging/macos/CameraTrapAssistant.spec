"""PyInstaller definition of the Camera Trap Assistant application bundle.

Run through packaging/macos/build.sh, which sets the environment variables read
below and signs the result. Invoke PyInstaller from the repository root so that
Path.cwd() resolves the project layout, exactly like the Windows spec.
"""

import json
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path.cwd()
app_dir = project_root / "CameraTrapAssistant"
src_dir = app_dir / "src"
packaging_dir = project_root / "packaging" / "macos"

version = json.loads((app_dir / "version.json").read_text(encoding="utf-8"))["version"]
bundle_identifier = os.environ.get(
    "CTA_BUNDLE_ID", "io.github.noebernigaud.CameraTrapAssistant"
)
minimum_system_version = os.environ.get("CTA_MIN_MACOS", "11.0")

icon_file = packaging_dir / "assets" / "AppIcon.icns"
icon = str(icon_file) if icon_file.is_file() else None

datas = [
    (str(app_dir / "resources"), "resources"),
    (str(src_dir / "models" / "weights"), "models/weights"),
    (str(src_dir / "models" / "model_manifest.json"), "models"),
    (str(src_dir / "models" / "LICENSE.txt"), "models"),
    (str(project_root / "LICENSE"), "."),
    (str(project_root / "THIRD_PARTY_NOTICES.md"), "."),
    (str(project_root / "CITATION.cff"), "."),
]

# build.sh resolves the exact dependency set before packaging so that the
# manifest is signed together with the rest of the bundle.
dependencies_file = os.environ.get("CTA_DEPENDENCIES_FILE", "")
if dependencies_file and Path(dependencies_file).is_file():
    datas.append((dependencies_file, "."))

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
    runtime_hooks=[str(packaging_dir / "runtime_hooks" / "cv2_loader.py")],
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
    # Stripping and UPX rewrite Mach-O headers, which invalidates code
    # signatures and makes notarization fail. Both stay disabled on macOS.
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="CameraTrapAssistant",
)

app = BUNDLE(
    coll,
    name="Camera Trap Assistant.app",
    icon=icon,
    bundle_identifier=bundle_identifier,
    version=version,
    info_plist={
        "CFBundleName": "Camera Trap Assistant",
        "CFBundleDisplayName": "Camera Trap Assistant",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "CFBundleIdentifier": bundle_identifier,
        "LSMinimumSystemVersion": minimum_system_version,
        "LSApplicationCategoryType": "public.app-category.photography",
        "NSHighResolutionCapable": True,
        # The interface follows the system appearance.
        "NSRequiresAquaSystemAppearance": False,
        "NSHumanReadableCopyright": (
            "Camera Trap Assistant. Includes models and source code from the "
            "DeepFaune project. See THIRD_PARTY_NOTICES.md."
        ),
        # Camera trap media usually lives on removable cards or in the standard
        # user folders. These strings are what macOS shows in its access
        # prompts, so they explain why the application needs the folder.
        "NSDesktopFolderUsageDescription": (
            "Camera Trap Assistant needs access to read and organize the "
            "camera trap media you select on your Desktop."
        ),
        "NSDocumentsFolderUsageDescription": (
            "Camera Trap Assistant needs access to read and organize the "
            "camera trap media you select in your Documents folder."
        ),
        "NSDownloadsFolderUsageDescription": (
            "Camera Trap Assistant needs access to read and organize the "
            "camera trap media you select in your Downloads folder."
        ),
        "NSRemovableVolumeUsageDescription": (
            "Camera Trap Assistant needs access to read camera trap media "
            "directly from memory cards and external drives."
        ),
        "NSNetworkVolumeUsageDescription": (
            "Camera Trap Assistant needs access to read camera trap media "
            "stored on network volumes."
        ),
    },
)

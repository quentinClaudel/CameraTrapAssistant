# Windows Release Packaging

This directory owns the public Windows distribution pipeline. It builds an
isolated application and installer; GitHub's generated source ZIP is not an
installable release.

## Files

- `build.ps1` orchestrates validation, packaging, smoke testing, and checksums.
- `CameraTrapAssistant.spec` defines the PyInstaller application bundle.
- `CameraTrapAssistant.iss` defines the Inno Setup installer.
- `artifacts/` contains generated release files and is ignored by Git.

## Prerequisites

- 64-bit Windows
- Python 3.10 or newer
- Git LFS with all model objects present
- Inno Setup 6 (`ISCC.exe`)
- At least 8 GiB of free disk space

## Build

From the repository root:

```powershell
.\packaging\windows\build.ps1
```

The build creates `.build-venv`, installs dependencies, runs tests, validates
the model manifest, invokes PyInstaller, smoke-tests the packaged executable,
and invokes Inno Setup. The packaged directory includes `DEPENDENCIES.txt`
with the exact resolved Python packages.

Generated release files:

```text
packaging/windows/artifacts/CameraTrapAssistant-<version>-Windows-x64-Setup.exe
packaging/windows/artifacts/SHA256SUMS.txt
```

Use `-SkipDependencyInstall` only when `.build-venv` is already complete.
Use `-SkipInstaller` to build and smoke-test only the PyInstaller directory.

## Release Checklist

1. Set the same version in `CameraTrapAssistant/version.json`,
   `CameraTrapAssistant/src/__init__.py`, and `CameraTrapAssistant.iss`.
2. Confirm that every bundled model and third-party component may be
   redistributed.
3. Run the complete build without skip flags.
4. Install on a clean Windows machine without Python or Git.
5. Test startup, image and video inference, GPS metadata operations, maps,
   uninstall, reinstall, and insufficient-disk-space behavior.
6. Attach the installer and `SHA256SUMS.txt` to the matching GitHub Release.
7. Keep automatic replacement disabled until upgrade and rollback paths have
   been tested end to end.

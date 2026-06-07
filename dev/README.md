# Developer Helpers

This directory contains Windows helpers for contributors running the source
checkout. These files are not part of the installed application.

## Responsibilities

- `setup.bat` creates the repository-local `.venv`, installs Python
  dependencies, and validates every bundled AI model.
- `run.bat` launches `CameraTrapAssistant/src/main.py` with `pythonw.exe`.
- `check-release.bat` compares the local version with GitHub Releases. It may
  open the Releases page, but it never replaces application files.

The root `run-source.bat` is the convenient entry point: it calls `setup.bat`
when `.venv` is missing, then calls `run.bat`.

## Requirements

- Windows 10 or newer
- Python 3.10 or newer
- Git LFS with all model files downloaded

From the repository root:

```bat
git lfs pull
dev\setup.bat
dev\run.bat
```

Non-technical users should install an official release instead of using these
developer helpers.

# Developer Workflow

The application can be run directly with Python. Building PyInstaller or the
Windows installer is not necessary for normal development checks.

## Platform-Neutral Setup

Requirements:

- Python 3.10 or newer
- Git LFS
- Platform-compatible builds of the dependencies in
  `CameraTrapAssistant/requirements.txt`

From the repository root, make sure the model files are present:

```bash
git lfs install
git lfs pull
```

Create `.venv` and install dependencies on Windows PowerShell:

```powershell
python3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r CameraTrapAssistant\requirements.txt
```

Or on macOS and Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r CameraTrapAssistant/requirements.txt
```

Using the virtual environment's Python explicitly means shell activation is
optional.

## Launch the Application

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe CameraTrapAssistant\src\main.py
```

macOS or Linux:

```bash
./.venv/bin/python CameraTrapAssistant/src/main.py
```

The app validates the model manifest at startup. If it reports Git LFS pointer
files, run `git lfs pull` again.

The repository currently bundles the Windows ExifTool executable. The GUI can
be launched on other platforms for development, but GPS metadata operations
need a platform-specific ExifTool implementation.

## Run Tests

Run the complete suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run a single test file by filename pattern:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_exiftool_interface.py" -v
```

Tests use the standard-library `unittest` runner. Keep tests under `tests/`
with filenames beginning with `test_` so discovery includes them.

## Optional Windows Helpers

- `setup.bat` creates `.venv`, installs dependencies, and validates the models.
- `run.bat` launches the source application with `pythonw.exe`.
- `check-release.bat` checks GitHub Releases without replacing local files.
- The root `run-source.bat` runs setup when needed and then launches the app.

These wrappers perform the same basic steps as the direct Python commands
above. They are conveniences, not requirements for development.

Non-technical users should install an official release instead of using these
developer helpers.

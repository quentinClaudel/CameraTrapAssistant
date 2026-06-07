# Tests

The project uses Python's built-in `unittest` framework. Test modules live in
this directory and must be named `test_*.py` for automatic discovery.

Return to the [developer and contributor guide](../dev/README.md) for
environment setup, source launch instructions, and the pull-request workflow.

## Run All Tests

Create `.venv` and install the project dependencies using the
[development setup](../dev/README.md#development-setup). Then run this command
from the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS or Linux:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Run Focused Tests

Run one test file:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_geocoding.py" -v
```

On macOS or Linux, use the same command with `./.venv/bin/python`.

Run one test class or method by adding `tests` to the import path:

```powershell
$env:PYTHONPATH = "tests"
.\.venv\Scripts\python.exe -m unittest test_geocoding.GeocodingTests -v
```

The equivalent macOS or Linux command is:

```bash
PYTHONPATH=tests ./.venv/bin/python -m unittest test_geocoding.GeocodingTests -v
```

## Add Tests

- Put tests in `tests/`.
- Name modules `test_*.py`.
- Prefer focused unit tests for changed behavior.
- Add broader coverage when changing shared workflows or external-tool
  integration.
- Keep tests independent of personal files, credentials, network availability,
  and machine-specific paths.

## Release Verification

`packaging/windows/build.ps1` runs the complete suite before model validation,
PyInstaller packaging, and the packaged-application smoke test. A release build
stops immediately if any test fails.

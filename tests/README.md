# Tests

The project uses Python's built-in `unittest` framework. Test modules live in
this directory and must be named `test_*.py` for automatic discovery.

## Run All Tests

Create `.venv` and install the project dependencies using the
[developer workflow](../dev/README.md). Then run this command from the
repository root on Windows:

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

Run one test class or method by adding `tests` to the import path:

```powershell
$env:PYTHONPATH = "tests"
.\.venv\Scripts\python.exe -m unittest test_geocoding.GeocodingTests -v
```

## Release Verification

`packaging/windows/build.ps1` runs the complete suite before model validation,
PyInstaller packaging, and the packaged-application smoke test. A release build
stops immediately if any test fails.

# Camera Trap Assistant

Camera Trap Assistant is a non-commercial, open-source desktop application for
detecting and classifying wildlife in camera-trap images and videos.

It uses AI models and selected source code from
[DeepFaune](https://deepfaune.pages.math.cnrs.fr/software/), a CNRS project.
Camera Trap Assistant is independent and is not affiliated with or endorsed by
CNRS or the DeepFaune authors.

## Install on Windows

Download `CameraTrapAssistant-<version>-Windows-x64-Setup.exe` and
`SHA256SUMS.txt` from the
[GitHub Releases page](https://github.com/noebernigaud/CameraTrapAssistant/releases).
Verify the checksum, run the installer, then launch the application from the
Start menu.

The installer includes an isolated runtime, verified AI models, and ExifTool.
Users do not need Python, Git, or Git LFS. Automatic application replacement
is intentionally disabled for v1.

## Repository Architecture

```text
CameraTrapAssistant/
  src/
    core/                 Feature and domain logic
    gui/                  Windows, widgets, and GUI helpers
    models/               DeepFaune integration, manifest, and model weights
    utils/                Shared infrastructure and external-service adapters
    config/               Runtime configuration code
    main.py               Application entry point
  resources/
    icons/                User-interface images
    config/               Packaged default configuration
    third_party/          Bundled runtime files, grouped by platform
  requirements.txt        Runtime Python dependencies
  version.json            Release metadata
dev/                      Source-checkout helpers for contributors
packaging/windows/        Windows build and installer definitions
tests/                    Automated tests
run-source.bat            Convenient Windows source launcher
LICENSE                   Project source license
THIRD_PARTY_NOTICES.md    External code, models, services, and assets
CITATION.cff              Citation metadata
```

The boundaries are intentional: application behavior belongs under
`CameraTrapAssistant`, contributor conveniences belong under `dev`, and
generated release work belongs under `packaging`.

Platform-specific distribution work should follow the same shape:
`packaging/<platform>` for build definitions and
`resources/third_party/<platform>` for bundled native components. This gives a
macOS packager a clear place to add its installer and native dependencies.

## Run from Source

Source development requires Windows, Python 3.10 or newer, and Git LFS. The
setup creates a repository-local `.venv`; it does not modify the user's global
Python environment.

```bat
git lfs install
git clone https://github.com/noebernigaud/CameraTrapAssistant.git
cd CameraTrapAssistant
git lfs pull
dev\setup.bat
dev\run.bat
```

Alternatively, run `run-source.bat` to set up the environment when needed and
launch the application. Model sizes and SHA-256 hashes are validated before
the AI libraries load. See [`dev/README.md`](dev/README.md) for helper
responsibilities.

## Run the Tests

The test suite uses Python's built-in `unittest` framework; no separate test
runner such as pytest is required. On Windows, first run `dev\setup.bat` to
create `.venv`. Then execute this from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To run one test file:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_geocoding.py" -v
```

On macOS or Linux, use `./.venv/bin/python` instead of
`.\.venv\Scripts\python.exe` after creating a virtual environment and
installing `CameraTrapAssistant/requirements.txt`. The Windows release build
also runs the complete suite automatically before packaging. More details are in
[`tests/README.md`](tests/README.md).

## Build a Windows Release

Release builds use PyInstaller in one-directory mode and Inno Setup 6:

```powershell
.\packaging\windows\build.ps1
```

The build runs tests, validates models, packages and smoke-tests the
application, creates the installer, and writes its checksum under
`packaging/windows/artifacts`. See the
[Windows packaging guide](packaging/windows/README.md) for prerequisites and
the release checklist.

## Versioning

Before a release, set the same version in:

- `CameraTrapAssistant/version.json`
- `CameraTrapAssistant/src/__init__.py`
- `packaging/windows/CameraTrapAssistant.iss`

Then run the complete build, test the installer on a clean Windows machine,
and publish the installer with `SHA256SUMS.txt` in a matching GitHub Release.

## License and Attribution

Project-original source code is copyright (c) 2025-2026 Noe Bernigaud and is
distributed under the [CeCILL v2.1 license](LICENSE). Adapted DeepFaune source
files retain their CNRS copyright and CeCILL notices.

The bundled DeepFaune model weights are licensed separately under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Other models,
dependencies, bundled software, services, and brand assets have their own
terms. Review [Third-Party Notices](THIRD_PARTY_NOTICES.md) before
redistributing the application.

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Research and
publications using the AI models should also acknowledge and cite DeepFaune
according to its official documentation.

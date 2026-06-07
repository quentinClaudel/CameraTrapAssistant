# Developing and Contributing

This guide is for contributors working from a source checkout. Building an
installer is not required for normal development.

- New user? Start with [Install and Use](../README.md#install-and-use).
- Working on tests? See the [test guide](../tests/README.md).
- Preparing a Windows release? See the
  [Windows packaging guide](../packaging/windows/README.md).

## Development Setup

### Requirements

- Python 3.10 or newer
- Git
- Git LFS
- Platform-compatible versions of the packages in
  `CameraTrapAssistant/requirements.txt`

Fork or clone the repository, then download the model files managed by Git
LFS:

```bash
git clone https://github.com/noebernigaud/CameraTrapAssistant.git
cd CameraTrapAssistant
git lfs install
git lfs pull
```

Create a repository-local virtual environment and install dependencies.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r CameraTrapAssistant\requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r CameraTrapAssistant/requirements.txt
```

The commands use the virtual environment's Python directly, so activating the
environment is optional.

## Run from Source

Run commands from the repository root.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe CameraTrapAssistant\src\main.py
```

macOS or Linux:

```bash
./.venv/bin/python CameraTrapAssistant/src/main.py
```

After initial setup, this is the only command needed for most development
checks. The application validates the model manifest at startup. If it reports
Git LFS pointer files, run `git lfs pull` again.

The repository currently bundles only the Windows ExifTool executable. The GUI
can be launched on macOS and Linux, but GPS metadata operations require a
platform-specific ExifTool integration.

## Run Tests

Run the complete suite before submitting a change.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS or Linux:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

Tests use Python's standard-library `unittest` runner. The
[test guide](../tests/README.md) explains focused test commands and discovery
conventions.

## Repository Architecture

```text
CameraTrapAssistant/
  src/
    core/                 Feature and domain logic
    gui/                  Windows, widgets, and GUI helpers
    models/               DeepFaune integration, manifest, and model weights
    utils/                Shared infrastructure and service adapters
    config/               Runtime option types
    main.py               Application entry point
  resources/
    icons/                User-interface images
    third_party/          Bundled native components by platform
  requirements.txt        Runtime Python dependencies
  version.json            Release metadata
dev/                      Source-checkout helpers and this guide
packaging/windows/        Windows build and installer definitions
tests/                    Automated tests
run-source.bat            Optional Windows source launcher
LICENSE                   Project source license
THIRD_PARTY_NOTICES.md    External code, models, services, and assets
CITATION.cff              Citation metadata
```

Keep application behavior under `CameraTrapAssistant`, developer conveniences
under `dev`, platform builds under `packaging/<platform>`, and bundled native
dependencies under `CameraTrapAssistant/resources/third_party/<platform>`.

## Contribution Workflow

1. Check the [issue tracker](https://github.com/noebernigaud/CameraTrapAssistant/issues)
   for related work.
2. For a large behavior or architecture change, open an issue before investing
   heavily so the approach can be discussed.
3. Create a focused branch from the current development branch.
4. Make the smallest coherent change and add or update tests when behavior
   changes.
5. Run the relevant tests and, for GUI changes, launch the application from
   source.
6. Update user or developer documentation when commands, workflows, options,
   outputs, or platform support change.
7. Open a pull request describing the problem, the solution, and how it was
   verified.

Keep unrelated refactors out of a focused pull request. Do not replace model
weights, bundled software, or license files without documenting provenance,
redistribution terms, and release impact.

## Prepare a Pull Request

Before opening a pull request, confirm:

- The application starts from source.
- Relevant tests pass.
- New behavior has focused test coverage where practical.
- User-facing changes are documented in the root README.
- Developer, test, or packaging commands are updated in their corresponding
  README.
- No credentials, private media, personal location data, build output, or
  local virtual environments are included.
- New dependencies and assets have compatible licenses and are recorded in
  `THIRD_PARTY_NOTICES.md`.

In the pull-request description, include the commands you ran and any platform
or feature that you could not test.

## Optional Windows Helpers

These wrappers perform the same basic work as the direct Python commands:

- `dev/setup.bat` creates `.venv`, installs dependencies, and validates models.
- `dev/run.bat` launches the source application with `pythonw.exe`.
- `dev/check-release.bat` checks GitHub Releases without replacing local files.
- `run-source.bat` at the repository root runs setup when needed and launches
  the application.

They are conveniences, not requirements. Non-technical users should install an
official release rather than use the developer helpers.

## Release Work

Do not use GitHub's generated source ZIP as an installable application: Git
LFS model content is not guaranteed to be present. Public packages must be
built and validated through a platform packaging pipeline.

The current Windows pipeline runs tests, validates model checksums, packages
the application, smoke-tests it, creates an installer, and writes release
checksums. Follow the [Windows packaging guide](../packaging/windows/README.md)
for its prerequisites and checklist.

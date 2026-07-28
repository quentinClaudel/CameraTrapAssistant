# macOS Release Packaging

This directory owns the public macOS distribution pipeline. It builds an
isolated application bundle and the disk image that users download; GitHub's
generated source ZIP is not an installable release.

This guide is for release maintainers. For everyday development, use the
[developer and contributor guide](../../dev/README.md). For installation as an
end user, see [Install and Use](../../README.md#install-and-use).

## Files

- `build.sh` orchestrates validation, packaging, signing, smoke testing, disk
  image assembly, and checksums.
- `CameraTrapAssistant.spec` defines the PyInstaller application bundle and its
  `Info.plist`.
- `entitlements.plist` declares the hardened runtime exceptions a frozen Python
  application needs.
- `make-dmg.sh` defines the disk image: the application, the alias of the
  Applications folder, and the installer window layout.
- `notarize.sh` submits an artifact to Apple and staples the ticket.
- `make-icons.py` draws the application icon, the volume icon, and the disk
  image background from code.
- `check-deployment-target.py` reports the oldest macOS release that can run a
  built bundle.
- `runtime_hooks/` holds the code that runs inside the packaged application
  before the first import.
- `fetch-exiftool.sh` stages the macOS copy of ExifTool into the repository.
- `assets/` contains the generated artwork.
- `artifacts/` contains generated release files and is ignored by Git.

## Prerequisites

- macOS 12 or newer on Apple silicon
- Xcode command line tools (`xcode-select --install`)
- Python 3.10 or newer **with tkinter**, from a portable interpreter
- Git LFS with all model objects present
- At least 15 GiB of free disk space

### Choosing the interpreter

The application bundle inherits the deployment target of the interpreter that
builds it. This is the detail that decides who can run the release:

| Interpreter | Oldest macOS the release supports |
| --- | --- |
| [python.org macOS installer](https://www.python.org/downloads/macos/) | macOS 10.13 or 11, as documented by the installer |
| `uv python install 3.12` | macOS 11 |
| Homebrew `python@3.x` | the macOS release the bottle was built on, often the current one |

Homebrew's interpreter produces a bundle that runs on the build machine and
fails to launch for everyone on an older system, so `build.sh` prefers the
portable options and refuses interpreters without tkinter.

The interpreter is only half the answer: a dependency can raise the floor on
its own. Recent NumPy wheels for Apple silicon are built against the macOS 14
SDK, so a bundle containing them cannot run on macOS 13 no matter which
interpreter built it. `build.sh` therefore measures the requirement across
every embedded binary and writes the measured value into
`LSMinimumSystemVersion` before signing, so the release never claims support it
cannot deliver. `CTA_MIN_MACOS` states what the project aims for; when the
measurement is higher, the build says which dependencies are responsible:

```bash
./.build-venv-macos/bin/python packaging/macos/check-deployment-target.py --list "dist/Camera Trap Assistant.app"
```

Pin those dependencies lower if older systems have to be supported.

`build.sh` selects an interpreter automatically. Override it with `--python` or
`CTA_PYTHON` when several are installed.

### The interpreter also decides the Tk threading rules

The interpreter chosen here brings its own Tk, and Tk 8.6 and Tk 9 do not treat
worker threads the same way. `_tkinter` decides whether to hand a cross-thread
Tk call to the main loop by reading `tcl_platform(threaded)`. Tcl 9 removed
that variable, because threads are always enabled, so `_tkinter` concludes the
interpreter is not threaded and runs the call inline on whichever thread made
it. On macOS a Tk dialog is an AppKit window, and AppKit terminates the process
when a window is created outside the main thread.

Calling `after()` from the worker thread is not a fix on its own. Under the
same conditions it registers the timer against the worker thread, whose event
queue nobody services, so the callback never runs: no crash, but no logs and no
completion dialog either.

`gui/utils/main_loop.py` therefore routes every worker-to-interface update
through a queue drained by a poll that only the main loop ever schedules. That
holds on Tk 8.6 and Tk 9 alike, so the build is free to follow whichever Tk the
interpreter ships. Application code must post through it and never touch a
widget from a worker thread; `tests/test_main_loop.py` and
`tests/test_gui_main_window.py` guard that.

Re-test a full analysis whenever the build interpreter changes. Both failures
appear only at run time, on macOS, and one of them is silent.

The build is native architecture only, because the PyTorch wheels are.

## Build

From the repository root:

```bash
./packaging/macos/build.sh
```

The build creates `.build-venv-macos`, installs dependencies, runs tests,
validates the model manifest, verifies the bundled ExifTool, draws any missing
artwork, invokes PyInstaller, checks the deployment target, signs the bundle
from the inside out, smoke-tests it, assembles the disk image, and writes
checksums. `DEPENDENCIES.txt` inside the bundle records the exact resolved
Python packages.

For faster development feedback, run the tests without packaging:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

See [`../../tests/README.md`](../../tests/README.md) for focused test commands.

Generated release files:

```text
packaging/macos/artifacts/CameraTrapAssistant-<version>-macOS-<arch>.dmg
packaging/macos/artifacts/SHA256SUMS.txt
```

Use `--skip-dependency-install` only when `.build-venv-macos` is already
complete. Use `--skip-tests` for a faster iteration. Use `--skip-dmg` to build
and smoke-test only the application bundle.

## Signing and Notarization

Without a signature, macOS refuses to open the application and offers no way
around it in the Finder. Three levels exist:

| Signature | Result for the user |
| --- | --- |
| Ad hoc, the default when no identity is given | Runs on the build machine only |
| Developer ID Application | Gatekeeper still warns on first launch |
| Developer ID Application plus notarization | Opens normally |

A public release needs the third. It requires a **Developer ID Application**
certificate from the Apple Developer Program. An "Apple Development" or
"Apple Distribution" certificate cannot be used for distribution outside the
App Store, and the notary service rejects it.

List the identities available in the keychain:

```bash
security find-identity -v -p codesigning
```

Store the notarization credentials once:

```bash
xcrun notarytool store-credentials CameraTrapAssistant --apple-id <apple id> --team-id <team id> --password <app specific password>
```

Then build a release that users can open without a warning:

```bash
./packaging/macos/build.sh --sign-identity "Developer ID Application: Your Name (TEAMID)" --notarize
```

`build.sh` signs every embedded binary before the bundle itself, because
signing only the outer bundle leaves the embedded extension modules unsigned
and notarization rejects that. The hardened runtime is enabled with the
exceptions in `entitlements.plist`; a frozen Python application cannot load its
own extension modules without them.

The disk image is signed as well and, with `--notarize`, submitted to Apple and
stapled. Stapling matters: it embeds the ticket so that first launch works even
without a network connection.

## Updating the Bundled ExifTool

The macOS bundle ships the ExifTool Unix distribution, which is pure Perl and
runs on the interpreter macOS provides at `/usr/bin/perl`. It contains no
compiled binaries, which keeps signing and notarization simple.

```bash
EXIFTOOL_VERSION=13.36 EXIFTOOL_SHA256=<checksum> ./packaging/macos/fetch-exiftool.sh
```

The script verifies the download against the pinned checksum, stages only the
runtime files, and confirms that the staged copy reports the expected version.
Commit the result and record the version in `THIRD_PARTY_NOTICES.md`, exactly
as for the Windows copy.

Keep the Windows and macOS copies on the same ExifTool version so that metadata
behaves identically on both platforms.

## Updating the Artwork

```bash
./.build-venv-macos/bin/python packaging/macos/make-icons.py --force
```

The icon and the disk image background are drawn from code so that they never
drift from the packaging scripts. The icon positions in `make-dmg.sh` and the
arrow drawn by `make-icons.py` share the same coordinates; change them
together.

## Release Checklist

1. Set the same version in `CameraTrapAssistant/version.json`,
   `CameraTrapAssistant/src/__init__.py`, and `packaging/windows/CameraTrapAssistant.iss`.
2. Confirm that every bundled model and third-party component may be
   redistributed.
3. Run the complete build without skip flags, signed and notarized.
4. Read the macOS version the build reports as supported and state it in the
   release notes.
5. Install on a clean Mac that has never built the project: open the disk
   image, drag the application into Applications, eject, and launch it from
   Launchpad.
6. Test startup, image and video inference, GPS metadata operations, maps, and
   the removable-volume access prompt with a real memory card.
7. Confirm that the first launch shows no Gatekeeper warning, including with
   the network disabled, which is what proves the ticket was stapled.
8. Attach the disk image and `SHA256SUMS.txt` to the matching GitHub Release.

#!/bin/bash
#
# Build the public macOS release of Camera Trap Assistant.
#
# The pipeline mirrors packaging/windows/build.ps1: validate, package, sign,
# smoke test, and publish checksums. It produces a signed application bundle
# and the disk image that users download.
#
# Usage:
#   ./packaging/macos/build.sh [options]
#
# Options:
#   --skip-dependency-install   Reuse .build-venv-macos as it is
#   --skip-tests                Do not run the test suite
#   --skip-dmg                  Stop after the signed application bundle
#   --notarize                  Submit the disk image to Apple and staple it
#   --sign-identity IDENTITY    Code signing identity, "-" for ad hoc
#   --python PATH               Interpreter used to create the build environment
#
# Environment:
#   CTA_PYTHON          Same as --python
#   CTA_SIGN_IDENTITY   Same as --sign-identity
#   CTA_NOTARY_PROFILE  notarytool keychain profile used by --notarize
#   CTA_BUNDLE_ID       Bundle identifier, defaults to the project identifier
#   CTA_MIN_MACOS       Declared LSMinimumSystemVersion, defaults to 11.0
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
APP_DIR="${PROJECT_ROOT}/CameraTrapAssistant"
BUILD_VENV="${PROJECT_ROOT}/.build-venv-macos"
BUILD_PYTHON="${BUILD_VENV}/bin/python"
SPEC_FILE="${SCRIPT_DIR}/CameraTrapAssistant.spec"
ENTITLEMENTS="${SCRIPT_DIR}/entitlements.plist"
ARTIFACTS_DIR="${SCRIPT_DIR}/artifacts"
BUNDLE_NAME="Camera Trap Assistant.app"
APP_BUNDLE="${PROJECT_ROOT}/dist/${BUNDLE_NAME}"

SKIP_DEPENDENCY_INSTALL=0
SKIP_TESTS=0
SKIP_DMG=0
NOTARIZE=0
SIGN_IDENTITY="${CTA_SIGN_IDENTITY:-}"
SELECTED_PYTHON="${CTA_PYTHON:-}"

export CTA_BUNDLE_ID="${CTA_BUNDLE_ID:-io.github.noebernigaud.CameraTrapAssistant}"
export CTA_MIN_MACOS="${CTA_MIN_MACOS:-11.0}"

log() { printf '\n==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-dependency-install) SKIP_DEPENDENCY_INSTALL=1; shift ;;
        --skip-tests) SKIP_TESTS=1; shift ;;
        --skip-dmg) SKIP_DMG=1; shift ;;
        --notarize) NOTARIZE=1; shift ;;
        --sign-identity) SIGN_IDENTITY="$2"; shift 2 ;;
        --python) SELECTED_PYTHON="$2"; shift 2 ;;
        -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) fail "unknown option: $1" ;;
    esac
done

[[ "$(uname -s)" == "Darwin" ]] || fail "this build must run on macOS"

# Removing a directory is the only destructive step in this script, so it is
# constrained to the project tree, exactly like the Windows build.
remove_generated_directory() {
    local target="$1"
    local resolved
    resolved="$(cd -- "$(dirname -- "${target}")" 2>/dev/null && pwd)/$(basename -- "${target}")" || return 0
    case "${resolved}" in
        "${PROJECT_ROOT}"/*) ;;
        *) fail "refusing to remove a directory outside the project: ${resolved}" ;;
    esac
    [[ -e "${resolved}" ]] && rm -rf "${resolved}"
    return 0
}

# ---------------------------------------------------------------------------
# Interpreter selection
# ---------------------------------------------------------------------------

# A distributable bundle inherits the deployment target of the interpreter that
# builds it. Homebrew interpreters are compiled for the macOS release of the
# machine that bottled them, which silently produces an application that
# refuses to launch on older systems. The candidates below are ordered from the
# most portable to the least.
python_is_usable() {
    local candidate="$1"
    [[ -x "${candidate}" ]] || return 1
    "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
if sys.version_info < (3, 10):
    raise SystemExit(1)
import tkinter  # noqa: F401  the application is a Tk program
PY
}

describe_python() {
    local candidate="$1"
    "${candidate}" -c 'import sys, _tkinter; print(f"Python {sys.version.split()[0]}, Tk {_tkinter.TK_VERSION}")'
}

select_python() {
    if [[ -n "${SELECTED_PYTHON}" ]]; then
        python_is_usable "${SELECTED_PYTHON}" ||
            fail "${SELECTED_PYTHON} is not usable: Python 3.10 or newer with tkinter is required"
        printf '%s' "${SELECTED_PYTHON}"
        return
    fi

    local candidates=()
    # python.org framework builds, newest first: the reference interpreter for
    # redistributable macOS applications.
    while IFS= read -r candidate; do
        candidates+=("${candidate}")
    done < <(ls -r /Library/Frameworks/Python.framework/Versions/*/bin/python3 2>/dev/null || true)

    # Portable standalone builds managed by uv target macOS 11 and ship Tk.
    if command -v uv >/dev/null 2>&1; then
        local uv_python
        for version in 3.12 3.13 3.11; do
            uv_python="$(uv python find "${version}" 2>/dev/null || true)"
            [[ -n "${uv_python}" ]] && candidates+=("${uv_python}")
        done
    fi

    candidates+=("$(command -v python3 || true)")

    for candidate in "${candidates[@]}"; do
        if python_is_usable "${candidate}"; then
            printf '%s' "${candidate}"
            return
        fi
    done

    fail "no usable interpreter found.
  The build needs Python 3.10 or newer with tkinter support. Install the
  official macOS package from https://www.python.org/downloads/macos/, or run
  'uv python install 3.12', then pass --python if it is not detected."
}

# ---------------------------------------------------------------------------
# Code signing
# ---------------------------------------------------------------------------

# codesign must be applied from the inside out: every nested binary first, the
# bundle last. Signing the bundle alone leaves the embedded extension modules
# unsigned and notarization rejects it.
list_macho_files() {
    "${BUILD_PYTHON}" - "$1" <<'PY'
import pathlib
import sys

MAGICS = {
    b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce",
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",
}

for path in pathlib.Path(sys.argv[1]).rglob("*"):
    if path.is_symlink() or not path.is_file():
        continue
    try:
        with path.open("rb") as handle:
            magic = handle.read(4)
    except OSError:
        continue
    if magic in MAGICS:
        print(path)
PY
}

sign_bundle() {
    local identity="$1"
    local timestamp_flag="--timestamp"
    [[ "${identity}" == "-" ]] && timestamp_flag="--timestamp=none"

    local macho_list
    macho_list="$(mktemp)"
    # Deepest paths first so that nested bundles are sealed before their parent.
    list_macho_files "${APP_BUNDLE}" |
        awk -F/ '{print NF"\t"$0}' | sort -rn | cut -f2- > "${macho_list}"

    local count
    count="$(wc -l < "${macho_list}" | tr -d ' ')"
    info "signing ${count} embedded binaries"
    while IFS= read -r binary; do
        codesign --force ${timestamp_flag} --options runtime \
            --sign "${identity}" "${binary}" >/dev/null 2>&1 ||
            fail "could not sign ${binary}"
    done < "${macho_list}"
    rm -f "${macho_list}"

    # Frameworks are signed as bundles so that their Info.plist is sealed too,
    # again from the inside out in case one embeds another.
    while IFS= read -r framework; do
        [[ -n "${framework}" ]] || continue
        info "signing framework $(basename "${framework}")"
        codesign --force ${timestamp_flag} --options runtime \
            --sign "${identity}" "${framework}" >/dev/null 2>&1 ||
            fail "could not sign ${framework}"
    done < <(find "${APP_BUNDLE}/Contents" -type d -name "*.framework" 2>/dev/null |
        awk -F/ '{print NF"\t"$0}' | sort -rn | cut -f2-)

    info "signing the application bundle"
    codesign --force ${timestamp_flag} --options runtime \
        --entitlements "${ENTITLEMENTS}" \
        --sign "${identity}" "${APP_BUNDLE}" ||
        fail "could not sign ${APP_BUNDLE}"
}

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

cd "${PROJECT_ROOT}"

VERSION="$(/usr/bin/python3 -c 'import json,sys;print(json.load(open("CameraTrapAssistant/version.json"))["version"])')"
ARCHITECTURE="$(uname -m)"
DMG_NAME="CameraTrapAssistant-${VERSION}-macOS-${ARCHITECTURE}.dmg"
DMG_PATH="${ARTIFACTS_DIR}/${DMG_NAME}"

log "Camera Trap Assistant ${VERSION} for macOS ${ARCHITECTURE}"

log "Selecting the build interpreter"
HOST_PYTHON="$(select_python)"
info "${HOST_PYTHON}"
info "$(describe_python "${HOST_PYTHON}")"

if [[ ! -x "${BUILD_PYTHON}" ]]; then
    log "Creating ${BUILD_VENV##*/}"
    "${HOST_PYTHON}" -m venv "${BUILD_VENV}"
fi

if (( ! SKIP_DEPENDENCY_INSTALL )); then
    log "Installing build dependencies"
    "${BUILD_PYTHON}" -m pip install --upgrade pip
    "${BUILD_PYTHON}" -m pip install -r "${APP_DIR}/requirements.txt"
    "${BUILD_PYTHON}" -m pip install "pyinstaller>=6,<7"
fi

if (( ! SKIP_TESTS )); then
    log "Running the test suite"
    "${BUILD_PYTHON}" -m unittest discover -s tests -v
fi

log "Validating the bundled models"
"${BUILD_PYTHON}" - <<'PY'
import sys
sys.path.insert(0, "CameraTrapAssistant/src")
from utils.model_manager import format_model_problems, validate_models

problems = validate_models()
if problems:
    print(format_model_problems(problems))
    raise SystemExit(1)
print("Model integrity checks passed.")
PY

log "Checking the bundled ExifTool"
"${BUILD_PYTHON}" - <<'PY'
import sys
sys.path.insert(0, "CameraTrapAssistant/src")
from utils.exiftool_interface import exiftool_is_available, run_exiftool

if not exiftool_is_available():
    print(
        "The macOS copy of ExifTool is missing. Run "
        "packaging/macos/fetch-exiftool.sh to stage it."
    )
    raise SystemExit(1)
result = run_exiftool(["-ver"])
if result.returncode != 0 or not result.stdout.strip():
    print(f"Bundled ExifTool failed: {result.stderr.strip()}")
    raise SystemExit(1)
print(f"ExifTool {result.stdout.strip()} is usable.")
PY

log "Preparing the application artwork"
"${BUILD_PYTHON}" "${SCRIPT_DIR}/make-icons.py"

log "Recording the resolved dependencies"
DEPENDENCIES_FILE="${PROJECT_ROOT}/build/DEPENDENCIES.txt"
mkdir -p "$(dirname "${DEPENDENCIES_FILE}")"
"${BUILD_PYTHON}" -m pip freeze > "${DEPENDENCIES_FILE}"
export CTA_DEPENDENCIES_FILE="${DEPENDENCIES_FILE}"

log "Packaging the application bundle"
remove_generated_directory "${PROJECT_ROOT}/dist"
"${BUILD_PYTHON}" -m PyInstaller --clean --noconfirm \
    --distpath "${PROJECT_ROOT}/dist" \
    --workpath "${PROJECT_ROOT}/build/pyinstaller" \
    "${SPEC_FILE}"
[[ -d "${APP_BUNDLE}" ]] || fail "PyInstaller did not produce ${BUNDLE_NAME}"

log "Checking the macOS deployment target"
"${BUILD_PYTHON}" "${SCRIPT_DIR}/check-deployment-target.py" "${APP_BUNDLE}"
REQUIRED_MACOS="$("${BUILD_PYTHON}" "${SCRIPT_DIR}/check-deployment-target.py" \
    --print-version "${APP_BUNDLE}")"

# The bundle must never claim to support a release it cannot run on. The target
# is what the project aims for; the measurement is what the wheels actually
# allow, and the measurement wins.
if [[ "$(printf '%s\n%s\n' "${CTA_MIN_MACOS}" "${REQUIRED_MACOS}" |
        sort -V | tail -1)" != "${CTA_MIN_MACOS}" ]]; then
    warn "the bundle requires macOS ${REQUIRED_MACOS}, newer than the ${CTA_MIN_MACOS} target.
  A dependency ships wheels built against a newer SDK. Run
    ${BUILD_PYTHON} ${SCRIPT_DIR}/check-deployment-target.py --list \"${APP_BUNDLE}\"
  to see which ones, and pin them lower if the older systems must be supported.
  LSMinimumSystemVersion is corrected to the measured value so that the release
  does not claim support it cannot deliver."
    /usr/libexec/PlistBuddy \
        -c "Set :LSMinimumSystemVersion ${REQUIRED_MACOS}" \
        "${APP_BUNDLE}/Contents/Info.plist"
fi
info "the release supports macOS ${REQUIRED_MACOS} and newer"

log "Signing the application bundle"
if [[ -z "${SIGN_IDENTITY}" ]]; then
    SIGN_IDENTITY="-"
    warn "no signing identity given, falling back to an ad hoc signature.
  An ad hoc signature runs on this machine but cannot be notarized, and other
  users will see a Gatekeeper warning. Pass --sign-identity with a
  \"Developer ID Application\" certificate for a public release."
fi
info "identity: ${SIGN_IDENTITY}"
sign_bundle "${SIGN_IDENTITY}"

log "Verifying the signature"
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"
if [[ "${SIGN_IDENTITY}" != "-" ]]; then
    spctl --assess --type exec --verbose=4 "${APP_BUNDLE}" ||
        warn "Gatekeeper does not accept the bundle yet; this is expected until
  it has been notarized."
fi

log "Smoke testing the packaged application"
"${APP_BUNDLE}/Contents/MacOS/CameraTrapAssistant" --smoke-test ||
    fail "the packaged application smoke test failed"
info "the packaged application loaded its models, icons, and ExifTool"

if (( SKIP_DMG )); then
    log "Application bundle ready: ${APP_BUNDLE}"
    exit 0
fi

log "Building the disk image"
mkdir -p "${ARTIFACTS_DIR}"
"${SCRIPT_DIR}/make-dmg.sh" \
    --app "${APP_BUNDLE}" \
    --output "${DMG_PATH}" \
    --volume-name "Camera Trap Assistant" \
    --sign-identity "${SIGN_IDENTITY}"

if (( NOTARIZE )); then
    log "Notarizing the disk image"
    "${SCRIPT_DIR}/notarize.sh" "${DMG_PATH}"
fi

log "Writing release checksums"
(
    cd "${ARTIFACTS_DIR}"
    shasum -a 256 "${DMG_NAME}" > SHA256SUMS.txt
)

log "Release disk image: ${DMG_PATH}"
info "$(du -h "${DMG_PATH}" | awk '{print $1}') on disk"
cat "${ARTIFACTS_DIR}/SHA256SUMS.txt"

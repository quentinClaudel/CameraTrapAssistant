#!/bin/bash
#
# Assemble the Camera Trap Assistant disk image.
#
# This is the macOS counterpart of CameraTrapAssistant.iss: it defines what the
# user sees when they open the download. The result is the layout macOS users
# expect, an application next to an alias of the Applications folder, so that
# installing is a single drag.
#
# It is a standalone script so that the disk image can be rebuilt without
# repackaging the application.
#
# Usage:
#   make-dmg.sh --app <path to .app> --output <path to .dmg> [options]
#
# Options:
#   --volume-name NAME    Name of the mounted volume
#   --background PATH     Background image for the installer window
#   --volume-icon PATH    .icns used as the volume icon
#   --sign-identity ID    Code signing identity applied to the disk image
#   --no-layout           Skip the Finder window layout step
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

APP_PATH=""
OUTPUT_PATH=""
VOLUME_NAME="Camera Trap Assistant"
BACKGROUND_PATH="${SCRIPT_DIR}/assets/dmg-background.tiff"
VOLUME_ICON_PATH="${SCRIPT_DIR}/assets/VolumeIcon.icns"
SIGN_IDENTITY=""
APPLY_LAYOUT=1

# Must stay consistent with the artwork produced by make-icons.py.
WINDOW_WIDTH=660
WINDOW_HEIGHT=420
ICON_SIZE=128
APP_ICON_X=180
APP_ICON_Y=205
APPLICATIONS_ICON_X=480
APPLICATIONS_ICON_Y=205

log() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --app) APP_PATH="$2"; shift 2 ;;
        --output) OUTPUT_PATH="$2"; shift 2 ;;
        --volume-name) VOLUME_NAME="$2"; shift 2 ;;
        --background) BACKGROUND_PATH="$2"; shift 2 ;;
        --volume-icon) VOLUME_ICON_PATH="$2"; shift 2 ;;
        --sign-identity) SIGN_IDENTITY="$2"; shift 2 ;;
        --no-layout) APPLY_LAYOUT=0; shift ;;
        -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) fail "unknown option: $1" ;;
    esac
done

[[ -n "${APP_PATH}" ]] || fail "--app is required"
[[ -n "${OUTPUT_PATH}" ]] || fail "--output is required"
[[ -d "${APP_PATH}" ]] || fail "application bundle not found: ${APP_PATH}"

APP_NAME="$(basename "${APP_PATH}")"
STAGING_DIR="$(mktemp -d)"
WRITABLE_DMG="$(mktemp -u).dmg"
ATTACH_PLIST="$(mktemp)"
MOUNT_POINT=""

cleanup() {
    # Detaching unconditionally: a detach of something that is not mounted is
    # harmless, and the mount can survive a failure at any later step.
    [[ -n "${MOUNT_POINT}" ]] &&
        hdiutil detach "${MOUNT_POINT}" -force >/dev/null 2>&1 || true
    rm -rf "${STAGING_DIR}"
    rm -f "${WRITABLE_DMG}" "${ATTACH_PLIST}"
}
trap cleanup EXIT

# Run a command with a wall clock limit. The Finder layout step needs macOS
# automation permission; without it osascript can block indefinitely, and a
# release build must never hang waiting for a dialog.
run_with_timeout() {
    local seconds="$1"; shift
    "$@" &
    local command_pid=$!
    (
        local waited=0
        while (( waited < seconds )); do
            kill -0 "${command_pid}" 2>/dev/null || exit 0
            sleep 1
            waited=$((waited + 1))
        done
        kill -TERM "${command_pid}" 2>/dev/null || true
    ) &
    local watchdog_pid=$!
    local status=0
    wait "${command_pid}" || status=$?
    kill "${watchdog_pid}" 2>/dev/null || true
    wait "${watchdog_pid}" 2>/dev/null || true
    return "${status}"
}

log "Staging ${APP_NAME}"
# ditto preserves extended attributes and code signatures; cp does not.
ditto "${APP_PATH}" "${STAGING_DIR}/${APP_NAME}"
ln -s /Applications "${STAGING_DIR}/Applications"

if [[ -f "${BACKGROUND_PATH}" ]]; then
    mkdir -p "${STAGING_DIR}/.background"
    BACKGROUND_NAME="background.${BACKGROUND_PATH##*.}"
    cp "${BACKGROUND_PATH}" "${STAGING_DIR}/.background/${BACKGROUND_NAME}"
else
    warn "background image not found: ${BACKGROUND_PATH}"
    BACKGROUND_NAME=""
fi

if [[ -f "${VOLUME_ICON_PATH}" ]]; then
    cp "${VOLUME_ICON_PATH}" "${STAGING_DIR}/.VolumeIcon.icns"
fi

log "Creating the writable image"
# No explicit size: hdiutil sizes the volume from the source folder and adds
# the slack the file system and the Finder layout need. A hand-computed size
# based on du underestimates the HFS+ allocation and the copy fails part way
# through with "No space left on device".
#
# HFS+ is used rather than APFS: it is what Finder layout metadata expects and
# it keeps the image readable on every supported macOS release.
hdiutil create \
    -srcfolder "${STAGING_DIR}" \
    -volname "${VOLUME_NAME}" \
    -fs HFS+ \
    -format UDRW \
    "${WRITABLE_DMG}" ||
    fail "hdiutil could not create the writable image"

log "Mounting the image"
# The image must mount under /Volumes rather than at a temporary mount point:
# Finder can only address a volume by name, and a volume mounted elsewhere is
# invisible to it, which silently defeats the layout step below. The real mount
# point is read back from hdiutil because macOS appends a suffix to the name
# when a volume of the same name is already mounted.
hdiutil attach "${WRITABLE_DMG}" \
    -nobrowse \
    -noautoopen \
    -plist > "${ATTACH_PLIST}" ||
    fail "hdiutil could not mount the writable image"

MOUNT_POINT="$(/usr/bin/python3 - "${ATTACH_PLIST}" <<'PY'
import plistlib
import sys

with open(sys.argv[1], "rb") as handle:
    entities = plistlib.load(handle)["system-entities"]
print(next(entity["mount-point"] for entity in entities if "mount-point" in entity))
PY
)"
[[ -d "${MOUNT_POINT}" ]] || fail "could not determine the mount point of the image"
MOUNTED_VOLUME_NAME="$(basename "${MOUNT_POINT}")"
log "Mounted at ${MOUNT_POINT}"

if [[ -f "${MOUNT_POINT}/.VolumeIcon.icns" ]]; then
    if command -v SetFile >/dev/null 2>&1; then
        SetFile -a C "${MOUNT_POINT}" || warn "could not flag the custom volume icon"
    elif xcrun --find SetFile >/dev/null 2>&1; then
        xcrun SetFile -a C "${MOUNT_POINT}" || warn "could not flag the custom volume icon"
    else
        warn "SetFile not available, the volume will use the generic icon"
    fi
fi

if (( APPLY_LAYOUT )); then
    log "Applying the Finder window layout"
    BACKGROUND_CLAUSE=""
    if [[ -n "${BACKGROUND_NAME}" ]]; then
        BACKGROUND_CLAUSE="set background picture of viewOptions to file \".background:${BACKGROUND_NAME}\""
    fi
    WINDOW_RIGHT=$(( 200 + WINDOW_WIDTH ))
    WINDOW_BOTTOM=$(( 160 + WINDOW_HEIGHT ))
    LAYOUT_SCRIPT=$(cat <<APPLESCRIPT
tell application "Finder"
    tell disk "${MOUNTED_VOLUME_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {200, 160, ${WINDOW_RIGHT}, ${WINDOW_BOTTOM}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to ${ICON_SIZE}
        set text size of viewOptions to 13
        ${BACKGROUND_CLAUSE}
        set position of item "${APP_NAME}" of container window to {${APP_ICON_X}, ${APP_ICON_Y}}
        set position of item "Applications" of container window to {${APPLICATIONS_ICON_X}, ${APPLICATIONS_ICON_Y}}
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
APPLESCRIPT
)
    LAYOUT_LOG="$(mktemp)"
    if run_with_timeout 90 osascript -e "${LAYOUT_SCRIPT}" > "${LAYOUT_LOG}" 2>&1; then
        log "Finder layout applied"
        rm -f "${LAYOUT_LOG}"
    else
        warn "the Finder layout could not be applied:
$(sed 's/^/  /' "${LAYOUT_LOG}")
  The disk image is still valid and still contains the Applications alias, but
  the window will open with the default Finder appearance. The usual cause is
  that the terminal has not been granted permission to control Finder in
  System Settings > Privacy & Security > Automation."
        rm -f "${LAYOUT_LOG}"
    fi
fi

sync
log "Unmounting the image"
hdiutil detach "${MOUNT_POINT}" -quiet

log "Compressing the final image"
rm -f "${OUTPUT_PATH}"
mkdir -p "$(dirname "${OUTPUT_PATH}")"
hdiutil convert "${WRITABLE_DMG}" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -quiet \
    -o "${OUTPUT_PATH}" ||
    fail "hdiutil could not compress the image"

if [[ -n "${SIGN_IDENTITY}" ]]; then
    log "Signing the disk image"
    TIMESTAMP_FLAG="--timestamp"
    [[ "${SIGN_IDENTITY}" == "-" ]] && TIMESTAMP_FLAG="--timestamp=none"
    codesign --force ${TIMESTAMP_FLAG} --sign "${SIGN_IDENTITY}" "${OUTPUT_PATH}"
    codesign --verify --verbose=2 "${OUTPUT_PATH}"
fi

log "Disk image ready: ${OUTPUT_PATH}"

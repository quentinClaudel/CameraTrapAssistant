#!/bin/bash
#
# Stage the macOS copy of ExifTool under
# CameraTrapAssistant/resources/third_party/macos/exiftool.
#
# The macOS bundle ships the ExifTool Unix distribution, which is a pure Perl
# program with no compiled components. It is executed through the Perl
# interpreter that macOS provides at /usr/bin/perl. Keeping it pure Perl means
# the bundle contains no unsigned Mach-O binaries, so notarization stays simple.
#
# Run this once per ExifTool version. The staged files are then committed to the
# repository, exactly like the Windows copy.
#
set -euo pipefail

EXIFTOOL_VERSION="${EXIFTOOL_VERSION:-13.36}"
# sha256 of https://github.com/exiftool/exiftool/archive/refs/tags/<version>.tar.gz
EXIFTOOL_SHA256="${EXIFTOOL_SHA256:-f70ecbcdccc18268d4d3c290faf8cf73b1cf128e3e7f8671e24d6604cae4dc73}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
DESTINATION="${PROJECT_ROOT}/CameraTrapAssistant/resources/third_party/macos/exiftool"
ARCHIVE_URL="https://github.com/exiftool/exiftool/archive/refs/tags/${EXIFTOOL_VERSION}.tar.gz"

log() { printf '==> %s\n' "$*"; }
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

ARCHIVE="${WORK_DIR}/exiftool-${EXIFTOOL_VERSION}.tar.gz"

log "Downloading ExifTool ${EXIFTOOL_VERSION}"
curl --fail --silent --show-error --location --max-time 300 \
    --output "${ARCHIVE}" "${ARCHIVE_URL}"

ACTUAL_SHA256="$(shasum -a 256 "${ARCHIVE}" | awk '{print $1}')"
if [[ "${ACTUAL_SHA256}" != "${EXIFTOOL_SHA256}" ]]; then
    fail "checksum mismatch for ${ARCHIVE_URL}
  expected ${EXIFTOOL_SHA256}
  actual   ${ACTUAL_SHA256}
Verify the download against https://exiftool.org/ before updating the pinned
checksum in this script."
fi
log "Checksum verified"

tar -xzf "${ARCHIVE}" -C "${WORK_DIR}"
SOURCE="${WORK_DIR}/exiftool-${EXIFTOOL_VERSION}"
[[ -f "${SOURCE}/exiftool" ]] || fail "the archive does not contain an exiftool script"
[[ -d "${SOURCE}/lib" ]] || fail "the archive does not contain the ExifTool lib directory"

log "Staging into ${DESTINATION#"${PROJECT_ROOT}/"}"
rm -rf "${DESTINATION}"
mkdir -p "${DESTINATION}"
# Only the runtime pieces are shipped: the driver script, its Perl library, and
# the license and readme required by the redistribution terms.
cp "${SOURCE}/exiftool" "${DESTINATION}/exiftool"
cp "${SOURCE}/LICENSE" "${DESTINATION}/LICENSE"
cp "${SOURCE}/README" "${DESTINATION}/README.txt"
cp -R "${SOURCE}/lib" "${DESTINATION}/lib"
chmod 0755 "${DESTINATION}/exiftool"
find "${DESTINATION}/lib" -type f -exec chmod 0644 {} +

STAGED_VERSION="$(/usr/bin/perl "${DESTINATION}/exiftool" -ver)"
[[ "${STAGED_VERSION}" == "${EXIFTOOL_VERSION}" ]] ||
    fail "staged ExifTool reports version ${STAGED_VERSION}, expected ${EXIFTOOL_VERSION}"

log "ExifTool ${STAGED_VERSION} staged and verified"
log "Record the version and provenance in THIRD_PARTY_NOTICES.md, then commit"

#!/bin/bash
#
# Notarize a Camera Trap Assistant artifact with Apple and staple the ticket.
#
# Notarization is what removes the "cannot be opened because the developer
# cannot be verified" dialog. It requires a "Developer ID Application"
# certificate, which is issued to Apple Developer Program members and is not
# the same certificate as "Apple Development" or "Apple Distribution".
#
# Set up the credentials once, then this script needs no secrets:
#
#   xcrun notarytool store-credentials CameraTrapAssistant \
#       --apple-id <apple id> --team-id <team id> --password <app specific password>
#
# The app specific password is created at https://account.apple.com, not the
# account password.
#
# Usage:
#   ./packaging/macos/notarize.sh <path to .dmg or .app> [--profile NAME]
#
# Environment:
#   CTA_NOTARY_PROFILE   notarytool keychain profile, defaults to CameraTrapAssistant
#
set -euo pipefail

TARGET=""
PROFILE="${CTA_NOTARY_PROFILE:-CameraTrapAssistant}"

log() { printf '==> %s\n' "$*"; }
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile) PROFILE="$2"; shift 2 ;;
        -h|--help) sed -n '2,28p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) TARGET="$1"; shift ;;
    esac
done

[[ -n "${TARGET}" ]] || fail "a .dmg or .app path is required"
[[ -e "${TARGET}" ]] || fail "not found: ${TARGET}"
command -v xcrun >/dev/null 2>&1 || fail "the Xcode command line tools are required"

# An ad hoc signature is accepted by codesign but always rejected by the
# notary service. Failing here saves a pointless round trip to Apple.
SIGNATURE_AUTHORITY="$(codesign --display --verbose=2 "${TARGET}" 2>&1 |
    awk -F'=' '/^Authority=/{print $2; exit}')"
if [[ -z "${SIGNATURE_AUTHORITY}" ]]; then
    fail "${TARGET} is not signed with a Developer ID certificate.
  Rebuild with: ./packaging/macos/build.sh --sign-identity \"Developer ID Application: ...\""
fi
log "Signed by ${SIGNATURE_AUTHORITY}"

SUBMISSION="${TARGET}"
CLEANUP=""
if [[ "${TARGET}" == *.app ]]; then
    # The notary service only accepts archives, so an application bundle is
    # zipped first. ditto keeps the signature intact.
    SUBMISSION="$(mktemp -u).zip"
    CLEANUP="${SUBMISSION}"
    log "Archiving the application bundle for submission"
    ditto -c -k --keepParent "${TARGET}" "${SUBMISSION}"
fi
trap '[[ -n "${CLEANUP}" ]] && rm -f "${CLEANUP}"' EXIT

log "Submitting to Apple with profile ${PROFILE} (this can take several minutes)"
xcrun notarytool submit "${SUBMISSION}" \
    --keychain-profile "${PROFILE}" \
    --wait ||
    fail "notarization failed.
  Inspect the rejection with:
    xcrun notarytool log <submission id> --keychain-profile ${PROFILE}"

log "Stapling the ticket"
xcrun stapler staple "${TARGET}"

log "Validating the stapled ticket"
xcrun stapler validate "${TARGET}"
spctl --assess --type open --context context:primary-signature --verbose=2 "${TARGET}" ||
    log "spctl reported a warning; check the output above"

log "Notarized: ${TARGET}"

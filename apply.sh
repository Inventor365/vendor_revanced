#!/usr/bin/env bash
#
# ReVanced ROM Integration Setup Script
#
# Idempotently prepares vendor/revanced prebuilts (Git LFS & arm64 native libs)
# and integrates/verifies the 4 required commits in frameworks/base and
# packages/apps/Settings.
#
# Usage:
#   bash vendor/revanced/apply.sh            # Apply/adapt missing commits & verify
#   bash vendor/revanced/apply.sh --check    # Read-only verification check
#   bash vendor/revanced/apply.sh --auto     # Quiet automatic mode (used by vendorsetup.sh)
#   bash vendor/revanced/apply.sh --no-commit # Apply to worktree without git commit
#
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATE_PY="${SCRIPT_DIR}/tools/revanced_integrate.py"

usage() {
    cat <<EOF
Usage: bash vendor/revanced/apply.sh [OPTIONS]

Prepares vendor/revanced prebuilts and integrates the 4 required ReVanced
framework and Settings commits into the target Android ROM source tree.

Options:
  --apply                 Apply or adapt any missing commits and verify (default)
  --check, --status       Read-only verification of prebuilts and all 4 commits
  --auto                  Quiet mode invoked automatically by vendorsetup.sh
  --no-commit             Apply source modifications without creating Git commits
  --root=<dir>            Explicit path to the Android ROM tree root
  --fwb-dir=<dir>         Override frameworks/base repository path
  --settings-dir=<dir>    Override packages/apps/Settings repository path
  --json-report=<file>    Write detailed JSON verification report to <file>
  -h, --help              Display this help message
EOF
}

PY_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --apply)
            ;;
        --check|--status)
            PY_ARGS+=("--check")
            ;;
        --auto|--quiet)
            PY_ARGS+=("--quiet")
            ;;
        --no-commit)
            PY_ARGS+=("--no-commit")
            ;;
        --root=*|--fwb-dir=*|--settings-dir=*|--json-report=*)
            PY_ARGS+=("$arg")
            ;;
        --root|--fwb-dir|--settings-dir|--json-report)
            PY_ARGS+=("$arg")
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            PY_ARGS+=("$arg")
            ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "[revanced] [ERR] python3 is required to run vendor/revanced/apply.sh" >&2
    exit 1
fi

exec python3 -I "$INTEGRATE_PY" "${PY_ARGS[@]}"

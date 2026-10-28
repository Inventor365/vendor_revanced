# Shebang is intentionally omitted - sourced by build/envsetup.sh
#
# Automatically verifies and prepares vendor/revanced integration when a device
# in the workspace inherits vendor/revanced/revanced.mk (or products/revanced.mk).
# Set REVANCED_SKIP_AUTO_SETUP=1 to skip automatic preparation during envsetup.

(
    if [ "${REVANCED_SKIP_AUTO_SETUP:-0}" = "1" ]; then
        exit 0
    fi

    REVANCED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TREE_ROOT="$(cd "${REVANCED_DIR}/../.." && pwd)"

    # Only run when vendor/revanced is inherited by a device or vendor makefile
    # (or when REVANCED_FORCE_SETUP=1 is set).
    if [ "${REVANCED_FORCE_SETUP:-0}" != "1" ]; then
        if ! grep -rqE "vendor/revanced/(products/)?revanced\.mk" \
                "${TREE_ROOT}/device" "${TREE_ROOT}/vendor" \
                --include="*.mk" --exclude-dir=".git" --exclude-dir="revanced" 2>/dev/null; then
            exit 0
        fi
    fi

    if ! bash "${REVANCED_DIR}/apply.sh" --auto; then
        echo "[revanced] [WARN] Automatic source setup reported an issue." >&2
        echo "[revanced] [WARN] Run 'bash vendor/revanced/apply.sh' to inspect and resolve before building." >&2
    fi
)

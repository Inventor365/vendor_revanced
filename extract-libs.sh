#!/usr/bin/env bash
#
# Extract arm64-v8a native libraries from the prebuilt YouTube and YTMusic APKs.
# Safe to run from any directory; validates APKs before replacing lib folders.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

extract_apk_libs() {
    local app_name="$1"
    local app_dir="common/product/app/${app_name}"
    local apk_path="${app_dir}/${app_name}.apk"
    local lib_dir="${app_dir}/lib"
    local tmp_dir="${app_dir}/.lib_extract_tmp"

    if [[ ! -f "$apk_path" ]]; then
        echo "[-] Error: APK not found at ${SCRIPT_DIR}/${apk_path}" >&2
        return 1
    fi

    if head -c 40 "$apk_path" 2>/dev/null | grep -q "^version https://git-lfs.github.com/spec/"; then
        echo "[-] Error: ${apk_path} is an unpulled Git LFS pointer. Run 'git -C ${SCRIPT_DIR} lfs pull' first." >&2
        return 1
    fi

    rm -rf "$tmp_dir"
    mkdir -p "$tmp_dir"
    unzip -q -o "$apk_path" "lib/arm64-v8a/*" -d "$tmp_dir"

    if [[ ! -d "$tmp_dir/lib/arm64-v8a" ]]; then
        rm -rf "$tmp_dir"
        echo "[-] Error: No lib/arm64-v8a/* entries found in ${apk_path}" >&2
        return 1
    fi

    mv "$tmp_dir/lib/arm64-v8a" "$tmp_dir/lib/arm64"
    touch "$tmp_dir/lib/placeholder.txt"

    rm -rf "$lib_dir"
    mv "$tmp_dir/lib" "$lib_dir"
    rm -rf "$tmp_dir"
    echo "[+] Extracted arm64 native libraries for ${app_name} -> ${lib_dir}/arm64"
}

extract_apk_libs "YouTube"
extract_apk_libs "YTMusic"

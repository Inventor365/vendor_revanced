#!/usr/bin/env python3
#
# ReVanced ROM Integration & Source Adaptation Engine
#
# Inspects the Android ROM workspace, verifies prebuilt APKs/libs and Git LFS
# state, audits frameworks/base and packages/apps/Settings, and idempotently
# applies or structurally adapts the 4 required ReVanced commits.
#
# SPDX-License-Identifier: Apache-2.0
#

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Required Commit Specifications (in dependency-safe application order)
# ---------------------------------------------------------------------------

FWB_COMMITS = [
    {
        "id": "fwb_commit_3_initial_hide",
        "prompt_label": "frameworks/base — commit 3 (chronological 1/3)",
        "sha": "1531342eb63352c7a616cc8c83a2c8edec2c4723",
        "equivalent_shas": [
            "1531342eb63352c7a616cc8c83a2c8edec2c4723",
            "e2bc392202a5",
            "e2b3c06e29c64ca15b4ff03f25f718ab8ad6cf74",
            "9fe7418b6dec",
            "bc71449a25b6b0d16d2b4e611cdc9939bd89bb54",
        ],
        "change_id": "I0499623e2580d5955ddf653bb7d5fc2861da002f",
        "subject": "base: Disable auto-updates for ReVanced Apps [1/2]",
        "author": "Quick ⚡ <quick@disroot.org>",
        "date": "Sat, 8 Nov 2025 14:56:19 +0530",
        "patch_file": "patches/frameworks_base/0001-base-Disable-auto-updates-for-ReVanced-Apps-1-2.patch",
        "files": [
            "core/java/android/app/ApplicationPackageManager.java",
        ],
        "message": (
            "base: Disable auto-updates for ReVanced Apps [1/2]\n\n"
            "* https://github.com/PixelLineage/vendor_revanced\n\n"
            "Adapted-From: 1531342eb63352c7a616cc8c83a2c8edec2c4723\n"
            "Change-Id: I0499623e2580d5955ddf653bb7d5fc2861da002f\n"
        ),
    },
    {
        "id": "fwb_commit_2_installer_fixup",
        "prompt_label": "frameworks/base — commit 2 (chronological 2/3)",
        "sha": "2a8351dd7fcd3e4300df10e793709939880284e8",
        "equivalent_shas": [
            "2a8351dd7fcd3e4300df10e793709939880284e8",
            "553540b6b70d",
            "3016ab1173de82c4468dc22de79257c5e799163c",
            "9397366b761c",
        ],
        "change_id": None,
        "subject": "fixup! base: Disable auto-updates for ReVanced Apps [1/2]",
        "author": "Quick ⚡ <quick@disroot.org>",
        "date": "Wed, 7 Jan 2026 00:07:42 +0530",
        "patch_file": "patches/frameworks_base/0002-fixup-base-Disable-auto-updates-for-ReVanced-Apps-1-.patch",
        "files": [
            "services/core/java/com/android/server/pm/PackageInstallerService.java",
        ],
        "message": (
            "fixup! base: Disable auto-updates for ReVanced Apps [1/2]\n\n"
            "Adapted-From: 2a8351dd7fcd3e4300df10e793709939880284e8\n"
        ),
    },
    {
        "id": "fwb_commit_1_harden_blocking",
        "prompt_label": "frameworks/base — commit 1 (chronological 3/3)",
        "sha": "5a97e2194499df3271770146168f75d81869241b",
        "equivalent_shas": [
            "5a97e2194499df3271770146168f75d81869241b",
            "ec37aea8a33b",
            "0f7693a542149f08de7004b970a7a758817ed4ef",
            "ce29ccf6ce60",
        ],
        "change_id": "I68db164cb4bd2fef815964612782caa3bd04f781",
        "subject": "base: Harden Revanced update blocking",
        "author": "Quick ⚡ <quick@disroot.org>",
        "date": "Mon, 25 May 2026 10:12:14 +0530",
        "patch_file": "patches/frameworks_base/0003-base-Harden-Revanced-update-blocking.patch",
        "files": [
            "core/java/android/app/ApplicationPackageManager.java",
            "services/core/java/com/android/server/pm/PackageInstallerService.java",
            "services/core/java/com/android/server/pm/PackageInstallerSession.java",
        ],
        "message": (
            "base: Harden Revanced update blocking\n\n"
            "* Hide revanced packages from Play Store direct and list queries\n"
            "* Abort Play Store update sessions after parsed package name is known\n"
            "* Use neutral managed-store naming to avoid logs detection\n\n"
            "Adapted-From: 5a97e2194499df3271770146168f75d81869241b\n"
            "Change-Id: I68db164cb4bd2fef815964612782caa3bd04f781\n"
        ),
    },
]

SETTINGS_COMMIT = {
    "id": "settings_commit_4_toggle",
    "prompt_label": "packages/apps/Settings — commit 4",
    "sha": "853d6a2aa1a7f68777679e4725a5f5a010bf37c7",
    "equivalent_shas": [
        "853d6a2aa1a7f68777679e4725a5f5a010bf37c7",
        "4a4ec91fd10",
        "a1508e8f10ddb503d809bd948066f782fad695fe",
    ],
    "change_id": "I40b593b1b16ef687086e6b5a1586bfe22057fa16",
    "subject": "Settings: Allow disabling ReVanced mods",
    "author": "Quick ⚡ <quick@disroot.org>",
    "date": "Mon, 19 Oct 2026 10:56:37 +0000",
    "patch_file": "patches/packages_apps_Settings/0001-Settings-Allow-disabling-ReVanced-mods.patch",
    "files": [
        "res/values/revanced_strings.xml",
        "res/xml/apps.xml",
        "src/com/android/settings/applications/AppDashboardFragment.java",
    ],
    "message": (
        "Settings: Allow disabling ReVanced mods\n\n"
        "Adds the ReVanced integration switch to Apps. Turning it on uninstalls\n"
        "YouTube/YT Music updates first, then sets persist.sys.revan.mod and\n"
        "reboots so the patched APKs are bind-mounted over the stock ones (see\n"
        "vendor/revanced); turning it off clears the property and reboots.\n\n"
        "Adapted-From: 853d6a2aa1a7f68777679e4725a5f5a010bf37c7\n"
        "Change-Id: I40b593b1b16ef687086e6b5a1586bfe22057fa16\n"
    ),
}

REQUIRED_SETTINGS_STRINGS = {
    "revan_toggle_title": "ReVanced Integration",
    "revan_toggle_summary": "Use ReVanced variants of YouTube and YT Music instead of stock apps",
    "revan_restart_dialog_title": "Restart device?",
    "revan_restart_dialog_message": "Restart now to apply this change.",
    "revan_restart_now": "Restart now",
}


# ---------------------------------------------------------------------------
# Logging & Subprocess Helpers
# ---------------------------------------------------------------------------

def log_info(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(f"[revanced] [INFO] {msg}")


def log_ok(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(f"[revanced] [OK]   {msg}")


def log_warn(msg: str) -> None:
    print(f"[revanced] [WARN] {msg}", file=sys.stderr)


def log_err(msg: str) -> None:
    print(f"[revanced] [ERR]  {msg}", file=sys.stderr)


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=True,
        env=merged_env,
    )


def write_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == content:
                return False
        except OSError:
            pass
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
    return True


# ---------------------------------------------------------------------------
# Tree Discovery & ROM Identification
# ---------------------------------------------------------------------------

def find_tree_root(start_dir: Path) -> Optional[Path]:
    cur = start_dir.resolve()
    while True:
        if (cur / "build" / "envsetup.sh").is_file() or (
            cur / "build" / "make" / "core" / "envsetup.mk"
        ).is_file():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def detect_rom_metadata(root_dir: Path) -> Dict[str, str]:
    info: Dict[str, str] = {
        "root": str(root_dir),
        "rom_name": "generic-aosp",
        "rom_branch": "unknown",
        "manifest_remote": "unknown",
    }

    if (root_dir / ".repo" / "manifests" / "penguin.xml").is_file():
        info["rom_name"] = "PenguinOS"
    elif (root_dir / "vendor" / "aospa").is_dir():
        info["rom_name"] = "AOSPA"
    elif (root_dir / "vendor" / "lineage").is_dir():
        info["rom_name"] = "LineageOS"
    elif (root_dir / "vendor" / "lunaris").is_dir() or (root_dir / "vendor" / "lumine").is_dir():
        info["rom_name"] = "Lunaris/LumineDroid"

    manifest_git = root_dir / ".repo" / "manifests"
    if (manifest_git / ".git").exists():
        r_branch = run_cmd(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=manifest_git, check=False
        )
        if r_branch.returncode == 0:
            info["rom_branch"] = r_branch.stdout.strip()
        r_rem = run_cmd(["git", "remote", "-v"], cwd=manifest_git, check=False)
        if r_rem.returncode == 0 and r_rem.stdout.strip():
            info["manifest_remote"] = r_rem.stdout.strip().splitlines()[0]

    version_mk = root_dir / "vendor" / "aospa" / "target" / "product" / "version.mk"
    if version_mk.is_file():
        text = version_mk.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"AOSPA_MAJOR_VERSION\s*:=\s*(\S+)", text)
        if m:
            info["rom_version"] = m.group(1)

    return info


# ---------------------------------------------------------------------------
# Git Repository Inspection
# ---------------------------------------------------------------------------

def inspect_git_repo(repo_dir: Path) -> Dict[str, object]:
    if not repo_dir.is_dir():
        raise RuntimeError(f"Repository directory does not exist: {repo_dir}")

    r_top = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=repo_dir, check=False)
    if r_top.returncode != 0:
        raise RuntimeError(f"Not a valid Git repository: {repo_dir}")

    head_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()
    head_subj = run_cmd(["git", "log", "-1", "--format=%s"], cwd=repo_dir).stdout.strip()
    sym_ref = run_cmd(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=repo_dir, check=False)
    branch = sym_ref.stdout.strip() if sym_ref.returncode == 0 else None

    upstream_res = run_cmd(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        cwd=repo_dir,
        check=False,
    )
    upstream = upstream_res.stdout.strip() if upstream_res.returncode == 0 else None

    remotes_res = run_cmd(["git", "remote", "-v"], cwd=repo_dir, check=False)
    remotes = {}
    if remotes_res.returncode == 0:
        for line in remotes_res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and "(fetch)" in line:
                remotes[parts[0]] = parts[1]

    status_res = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir)
    dirty_tracked = []
    untracked = []
    for line in status_res.stdout.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:]
        if code == "??":
            untracked.append(path)
        else:
            dirty_tracked.append(path)

    return {
        "path": str(repo_dir),
        "head_sha": head_sha,
        "head_subject": head_subj,
        "branch": branch,
        "detached": branch is None,
        "upstream": upstream,
        "remotes": remotes,
        "dirty_tracked": dirty_tracked,
        "untracked": untracked,
    }


def check_commit_in_history(repo_dir: Path, spec: Dict[str, object]) -> Optional[str]:
    # Inspect recent commits (last 100) in-memory in a single fast call (<5ms)
    # to avoid expensive graph walks across diverged AOSP branches.
    r_log = run_cmd(
        ["git", "log", "-n", "100", "--format=%x1e%H%x1f%B"],
        cwd=repo_dir,
        check=False,
    )
    if r_log.returncode == 0 and r_log.stdout:
        eq_prefixes = tuple(str(s) for s in spec.get("equivalent_shas", []))
        change_id = spec.get("change_id")
        orig_sha = str(spec["sha"])
        subj = str(spec["subject"])
        entries = []
        for entry in r_log.stdout.split("\x1e"):
            if "\x1f" not in entry:
                continue
            commit_hash, body = entry.split("\x1f", 1)
            first_line = body.splitlines()[0].strip() if body.splitlines() else ""
            entries.append((commit_hash.strip(), first_line, body))

        for commit_hash, _, _ in entries:
            if commit_hash.startswith(eq_prefixes):
                return commit_hash
        for commit_hash, _, body in entries:
            if f"Adapted-From: {orig_sha}" in body:
                return commit_hash
        if change_id:
            for commit_hash, _, body in entries:
                if f"Change-Id: {change_id}" in body:
                    return commit_hash
        for commit_hash, first_line, _ in entries:
            if first_line == subj:
                return commit_hash

    return None


def get_dirty_files_for_paths(repo_dir: Path, rel_paths: List[str]) -> List[str]:
    r = run_cmd(["git", "status", "--porcelain", "--"] + rel_paths, cwd=repo_dir, check=False)
    dirty = []
    for line in r.stdout.splitlines():
        if line.strip():
            dirty.append(line.strip())
    return dirty


# ---------------------------------------------------------------------------
# Prebuilt APKs, Native Libs, and Git LFS Verification
# ---------------------------------------------------------------------------

def is_lfs_pointer(file_path: Path) -> bool:
    if not file_path.is_file():
        return False
    try:
        with file_path.open("rb") as f:
            head = f.read(64)
        return head.startswith(b"version https://git-lfs.github.com/spec/")
    except OSError:
        return False


def is_valid_zip_archive(file_path: Path) -> bool:
    if not file_path.is_file():
        return False
    try:
        with file_path.open("rb") as f:
            magic = f.read(4)
        return magic == b"PK\x03\x04"
    except OSError:
        return False


def is_valid_elf64(file_path: Path) -> bool:
    if not file_path.is_file():
        return False
    try:
        with file_path.open("rb") as f:
            magic = f.read(5)
        return magic == b"\x7fELF\x02"
    except OSError:
        return False


def verify_and_prepare_prebuilts(revanced_dir: Path, apply_mode: bool, quiet: bool = False) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    apks = [
        revanced_dir / "common/product/app/YouTube/YouTube.apk",
        revanced_dir / "common/product/etc/rv/YouTube_patched.apk",
        revanced_dir / "common/product/app/YTMusic/YTMusic.apk",
        revanced_dir / "common/product/etc/rv/YTMusic_patched.apk",
    ]

    # Check if any APK is an unpulled Git LFS pointer
    needs_lfs = any(is_lfs_pointer(p) for p in apks)
    if needs_lfs and apply_mode:
        log_info("Detected Git LFS pointer files in vendor/revanced; running 'git lfs pull'...", quiet)
        r = run_cmd(["git", "lfs", "pull"], cwd=revanced_dir, check=False)
        if r.returncode != 0:
            errors.append(f"Failed to pull Git LFS objects in {revanced_dir}: {r.stderr.strip()}")

    for apk in apks:
        if not apk.is_file():
            errors.append(f"Missing prebuilt APK: {apk}")
        elif is_lfs_pointer(apk):
            errors.append(f"Prebuilt APK is an unpulled Git LFS pointer: {apk}")
        elif not is_valid_zip_archive(apk):
            errors.append(f"Prebuilt APK is not a valid ZIP/APK archive: {apk}")

    if errors:
        return False, errors

    # Verify extracted arm64 native libraries and placeholder.txt
    for app_name in ("YouTube", "YTMusic"):
        lib_dir = revanced_dir / f"common/product/app/{app_name}/lib"
        arm64_dir = lib_dir / "arm64"
        placeholder = lib_dir / "placeholder.txt"
        so_files = list(arm64_dir.glob("*.so")) if arm64_dir.is_dir() else []
        invalid_so = [s for s in so_files if is_lfs_pointer(s) or not is_valid_elf64(s)]

        if (not placeholder.is_file() or not so_files or invalid_so) and apply_mode:
            log_info(f"Extracting arm64 native libraries for {app_name} via extract-libs.sh...", quiet)
            r = run_cmd(["bash", str(revanced_dir / "extract-libs.sh")], cwd=revanced_dir, check=False)
            if r.returncode != 0:
                errors.append(f"extract-libs.sh failed for {app_name}: {r.stderr.strip()}")
                return False, errors
            so_files = list(arm64_dir.glob("*.so")) if arm64_dir.is_dir() else []
            invalid_so = [s for s in so_files if is_lfs_pointer(s) or not is_valid_elf64(s)]

        if not placeholder.is_file():
            errors.append(f"Missing native lib placeholder: {placeholder}")
        if not so_files:
            errors.append(f"No arm64 native libraries found in {arm64_dir}")
        if invalid_so:
            errors.append(
                f"Invalid or LFS-pointer native libraries in {arm64_dir}: "
                + ", ".join(p.name for p in invalid_so[:5])
            )

    init_rc = revanced_dir / "common/product/etc/init/init.rv.rc"
    sepolicy_te = revanced_dir / "sepolicy/private/revanced_init.te"
    if not init_rc.is_file():
        errors.append(f"Missing init script: {init_rc}")
    if not sepolicy_te.is_file():
        errors.append(f"Missing SELinux policy file: {sepolicy_te}")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Code-Level Verification for the 4 Required Commits
# ---------------------------------------------------------------------------

def check_brace_balance(java_text: str) -> bool:
    # Strip comments and string literals before counting braces
    cleaned = re.sub(r"//.*?$|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", "", java_text, flags=re.S | re.M)
    return cleaned.count("{") == cleaned.count("}")


def verify_fwb_commit_3_harden(fwb_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verifies the final hardened state (commit 5a97e2194499df3271770146168f75d81869241b)
    across ApplicationPackageManager.java, PackageInstallerService.java, and
    PackageInstallerSession.java.
    """
    issues: List[str] = []

    apm_path = fwb_dir / "core/java/android/app/ApplicationPackageManager.java"
    pis_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerService.java"
    psess_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerSession.java"

    for p in (apm_path, pis_path, psess_path):
        if not p.is_file():
            return False, [f"Missing file: {p}"]

    apm = apm_path.read_text(encoding="utf-8", errors="ignore")
    pis = pis_path.read_text(encoding="utf-8", errors="ignore")
    psess = psess_path.read_text(encoding="utf-8", errors="ignore")

    # 1. ApplicationPackageManager.java checks
    apm_required = [
        "import android.annotation.Nullable;",
        "import android.os.SystemProperties;",
        'private static final String PACKAGE_PLAY_STORE = "com.android.vending";',
        'private static final String PACKAGE_YOUTUBE = "com.google.android.youtube";',
        'private static final String PACKAGE_YOUTUBE_MUSIC = "com.google.android.apps.youtube.music";',
        'private static final String PROPERTY_MANAGED_STORE_UPDATES = "persist.sys.revan.mod";',
        "private boolean shouldHideManagedPackage(@Nullable String packageName)",
        "private boolean shouldHideManagedPackages()",
        "private static boolean isManagedPackage(@Nullable String packageName)",
        "res.removeIf(pi -> pi != null && isManagedPackage(pi.packageName));",
        "res.removeIf(ai -> ai != null && isManagedPackage(ai.packageName));",
    ]
    for token in apm_required:
        if token not in apm:
            issues.append(f"ApplicationPackageManager.java missing: {token}")

    if apm.count("if (shouldHideManagedPackage(packageName))") < 2:
        issues.append(
            "ApplicationPackageManager.java must guard both getPackageInfoAsUser and getApplicationInfoAsUser with shouldHideManagedPackage(packageName)"
        )
    if apm.count("private boolean shouldHideManagedPackage(") > 1:
        issues.append("ApplicationPackageManager.java has duplicate shouldHideManagedPackage definitions")
    if "BEGIN HIDE PATCH" in apm:
        issues.append("ApplicationPackageManager.java still contains unreplaced legacy ReVanHide block")
    if not check_brace_balance(apm):
        issues.append("ApplicationPackageManager.java has unbalanced braces")

    # 2. PackageInstallerService.java checks
    pis_required = [
        "import android.annotation.Nullable;",
        "import android.os.SystemProperties;",
        "import com.android.internal.util.ArrayUtils;",
        'private static final String PACKAGE_PLAY_STORE = "com.android.vending";',
        'private static final String PACKAGE_YOUTUBE = "com.google.android.youtube";',
        'private static final String PACKAGE_YOUTUBE_MUSIC = "com.google.android.apps.youtube.music";',
        'private static final String PROPERTY_MANAGED_STORE_UPDATES = "persist.sys.revan.mod";',
        "if (shouldBlockManagedStoreUpdate(installerPackageName, params.appPackageName))",
        "static boolean shouldBlockManagedStoreUpdate(@Nullable String installerPackageName,",
        "private boolean shouldBlockManagedStoreUpdate(@Nullable String packageName, int callingUid)",
        "private static boolean isManagedPackage(@Nullable String packageName)",
        "if (shouldBlockManagedStoreUpdate(packageName, Binder.getCallingUid()))",
    ]
    for token in pis_required:
        if token not in pis:
            issues.append(f"PackageInstallerService.java missing: {token}")

    if pis.count("private static boolean isManagedPackage(") > 1:
        issues.append("PackageInstallerService.java has duplicate isManagedPackage definitions")
    if "boolean blockrv =" in pis or "RevancedBlocker:" in pis:
        issues.append("PackageInstallerService.java still contains unreplaced legacy revanced blocker block")
    if not check_brace_balance(pis):
        issues.append("PackageInstallerService.java has unbalanced braces")

    # 3. PackageInstallerSession.java checks
    psess_required = [
        "import static android.content.pm.PackageManager.INSTALL_FAILED_ABORTED;",
        "child.enforceManagedStoreUpdateBlock();",
        "enforceManagedStoreUpdateBlock();",
        "if (e.error == INSTALL_FAILED_ABORTED)",
        "private void enforceManagedStoreUpdateBlock() throws PackageManagerException",
        "PackageInstallerService.shouldBlockManagedStoreUpdate(getInstallerPackageName(),",
    ]
    for token in psess_required:
        if token not in psess:
            issues.append(f"PackageInstallerSession.java missing: {token}")

    if psess.count("private void enforceManagedStoreUpdateBlock()") > 1:
        issues.append("PackageInstallerSession.java has duplicate enforceManagedStoreUpdateBlock definitions")
    if not check_brace_balance(psess):
        issues.append("PackageInstallerSession.java has unbalanced braces")

    return len(issues) == 0, issues


def verify_fwb_commit_1_initial(fwb_dir: Path) -> Tuple[bool, List[str]]:
    """
    Commit 1531342eb63352c7a616cc8c83a2c8edec2c4723 is satisfied either if the
    superseded hardened state (5a97e2194499df3271770146168f75d81869241b) is
    present, or if the initial ReVanHide filter is present in
    ApplicationPackageManager.java.
    """
    ok_harden, _ = verify_fwb_commit_3_harden(fwb_dir)
    if ok_harden:
        return True, []

    apm_path = fwb_dir / "core/java/android/app/ApplicationPackageManager.java"
    if not apm_path.is_file():
        return False, [f"Missing file: {apm_path}"]
    apm = apm_path.read_text(encoding="utf-8", errors="ignore")
    if (
        "BEGIN HIDE PATCH" in apm
        and 'SystemProperties.get("persist.sys.revan.mod"' in apm
        and '"com.google.android.youtube".equals(pkg)' in apm
    ):
        return True, []
    return False, ["ApplicationPackageManager.java does not have commit 1531342eb633 or hardened 5a97e2194499"]


def verify_fwb_commit_2_fixup(fwb_dir: Path) -> Tuple[bool, List[str]]:
    """
    Commit 2a8351dd7fcd3e4300df10e793709939880284e8 is satisfied either if the
    superseded hardened state (5a97e2194499df3271770146168f75d81869241b) is
    present, or if the initial revanced blocker is present in
    PackageInstallerService.java.
    """
    ok_harden, _ = verify_fwb_commit_3_harden(fwb_dir)
    if ok_harden:
        return True, []

    pis_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerService.java"
    if not pis_path.is_file():
        return False, [f"Missing file: {pis_path}"]
    pis = pis_path.read_text(encoding="utf-8", errors="ignore")
    if (
        "import android.os.SystemProperties;" in pis
        and "boolean blockrv =" in pis
        and "RevancedBlocker: blocking installExistingPackage" in pis
    ):
        return True, []
    return False, ["PackageInstallerService.java does not have commit 2a8351dd7fcd or hardened 5a97e2194499"]


def find_settings_string_occurrences(settings_dir: Path) -> Dict[str, List[Path]]:
    occurrences: Dict[str, List[Path]] = {k: [] for k in REQUIRED_SETTINGS_STRINGS}
    values_dir = settings_dir / "res/values"
    if not values_dir.is_dir():
        return occurrences
    for xml_file in sorted(values_dir.glob("*.xml")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for elem in root.findall("string"):
                name = elem.get("name")
                if name in occurrences:
                    occurrences[name].append(xml_file)
        except ET.ParseError:
            continue
    return occurrences


def verify_settings_commit_4(settings_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verifies commit 853d6a2aa1a7f68777679e4725a5f5a010bf37c7 in packages/apps/Settings:
    1. All 5 revan_* strings defined exactly once in res/values/*.xml.
    2. SwitchPreferenceCompat (key="persist_revan_mod") present once in res/xml/apps.xml.
    3. AppDashboardFragment.java has all imports, constants, onStart(),
       showRevanRestartDialog(), uninstallUpdatesThenEnable() with
       IPackageDeleteObserver & AtomicInteger, and reboot().
    """
    issues: List[str] = []

    apps_xml_path = settings_dir / "res/xml/apps.xml"
    frag_path = settings_dir / "src/com/android/settings/applications/AppDashboardFragment.java"

    if not apps_xml_path.is_file():
        issues.append(f"Missing file: {apps_xml_path}")
    if not frag_path.is_file():
        issues.append(f"Missing file: {frag_path}")
    if issues:
        return False, issues

    # 1. Check string resources
    str_occ = find_settings_string_occurrences(settings_dir)
    for name, files in str_occ.items():
        if len(files) == 0:
            issues.append(f"Missing string resource '{name}' in res/values/*.xml")
        elif len(files) > 1:
            issues.append(
                f"Duplicate string resource '{name}' in: " + ", ".join(str(f.name) for f in files)
            )

    # 2. Check res/xml/apps.xml
    try:
        apps_tree = ET.parse(apps_xml_path)
        apps_root = apps_tree.getroot()
        android_ns = "{http://schemas.android.com/apk/res/android}"
        revan_prefs = [
            el
            for el in apps_root.iter("SwitchPreferenceCompat")
            if el.get(f"{android_ns}key") == "persist_revan_mod"
        ]
        if len(revan_prefs) == 0:
            issues.append("res/xml/apps.xml missing SwitchPreferenceCompat with android:key='persist_revan_mod'")
        elif len(revan_prefs) > 1:
            issues.append("res/xml/apps.xml has duplicate SwitchPreferenceCompat with android:key='persist_revan_mod'")
        else:
            pref = revan_prefs[0]
            if pref.get(f"{android_ns}title") != "@string/revan_toggle_title":
                issues.append("res/xml/apps.xml persist_revan_mod has unexpected android:title")
            if pref.get(f"{android_ns}summary") != "@string/revan_toggle_summary":
                issues.append("res/xml/apps.xml persist_revan_mod has unexpected android:summary")
    except ET.ParseError as e:
        issues.append(f"res/xml/apps.xml is not valid XML: {e}")

    # 3. Check AppDashboardFragment.java
    frag = frag_path.read_text(encoding="utf-8", errors="ignore")
    frag_required = [
        "import android.content.pm.IPackageDeleteObserver;",
        "import android.content.pm.PackageManager;",
        "import android.os.PowerManager;",
        "import android.os.SystemProperties;",
        "import androidx.appcompat.app.AlertDialog;",
        "import androidx.preference.Preference;",
        "import androidx.preference.SwitchPreferenceCompat;",
        "import static android.os.UserHandle.USER_SYSTEM;",
        "import java.util.concurrent.atomic.AtomicInteger;",
        'private static final String REVAN_PREF_KEY = "persist_revan_mod";',
        'private static final String REVAN_PROP = "persist.sys.revan.mod";',
        '"com.google.android.youtube"',
        '"com.google.android.apps.youtube.music"',
        "showRevanRestartDialog(toggle, (Boolean) newVal);",
        "private void showRevanRestartDialog(SwitchPreferenceCompat toggle, boolean enabled)",
        "uninstallUpdatesThenEnable(context);",
        "private void uninstallUpdatesThenEnable(Context context)",
        "new IPackageDeleteObserver.Stub()",
        "pm.deletePackageAsUser(pkg, observer, 0, USER_SYSTEM);",
        "private void reboot(Context context)",
    ]
    for token in frag_required:
        if token not in frag:
            issues.append(f"AppDashboardFragment.java missing: {token}")

    if frag.count("private void showRevanRestartDialog(") > 1:
        issues.append("AppDashboardFragment.java has duplicate showRevanRestartDialog definitions")
    if frag.count("private void uninstallUpdatesThenEnable(") > 1:
        issues.append("AppDashboardFragment.java has duplicate uninstallUpdatesThenEnable definitions")
    if not check_brace_balance(frag):
        issues.append("AppDashboardFragment.java has unbalanced braces")

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Structural Source Adapters (Fallback when raw patch context differs across ROMs)
# ---------------------------------------------------------------------------

def ensure_java_import(content: str, import_stmt: str) -> str:
    if import_stmt in content:
        return content
    # Insert after the last import statement
    matches = list(re.finditer(r"^import\s+[^;]+;\s*$", content, flags=re.M))
    if not matches:
        raise RuntimeError(f"Could not find import block to insert: {import_stmt}")
    last = matches[-1]
    idx = last.end()
    return content[:idx] + "\n" + import_stmt + content[idx:]


def adapt_fwb_commit_1(fwb_dir: Path) -> None:
    """Structurally adapts commit 1531342eb63352c7a616cc8c83a2c8edec2c4723."""
    apm_path = fwb_dir / "core/java/android/app/ApplicationPackageManager.java"
    content = apm_path.read_text(encoding="utf-8")

    content = ensure_java_import(content, "import java.util.Iterator;")

    pattern = re.compile(
        r"(public\s+List<PackageInfo>\s+getInstalledPackagesAsUser\s*\(\s*PackageInfoFlags\s+flags\s*,\s*int\s+userId\s*\)\s*\{.*?"
        r"if\s*\(\s*parceledList\s*==\s*null\s*\)\s*\{\s*return\s+Collections\.emptyList\(\);\s*\}\s*)"
        r"return\s+parceledList\.getList\(\);",
        flags=re.S,
    )
    m = pattern.search(content)
    if not m:
        raise RuntimeError(
            "Incompatible ApplicationPackageManager.java: could not locate "
            "getInstalledPackagesAsUser(PackageInfoFlags, int) return site."
        )

    replacement_block = (
        "List<PackageInfo> res = parceledList.getList();\n\n"
        "            // --- BEGIN HIDE PATCH (skip only if persist.sys.revan.mod=false) ---\n"
        "            try {\n"
        '                String revProp = android.os.SystemProperties.get("persist.sys.revan.mod", "");\n'
        "                // Skip hiding only when explicitly disabled\n"
        '                if (!"false".equalsIgnoreCase(revProp)) {\n'
        "                    String caller = mContext.getOpPackageName();\n"
        '                    if ("com.android.vending".equals(caller)) {\n'
        "                        Iterator<PackageInfo> it = res.iterator();\n"
        "                        while (it.hasNext()) {\n"
        "                            PackageInfo pi = it.next();\n"
        "                            String pkg = pi.packageName;\n"
        '                            if ("com.google.android.youtube".equals(pkg)\n'
        '                                    || "com.google.android.apps.youtube.music".equals(pkg)) {\n'
        "                                it.remove();\n"
        "                            }\n"
        "                        }\n"
        '                        android.util.Log.i("ReVanHide",\n'
        '                            "Filtered YouTube + YouTube Music for Play Store");\n'
        "                    }\n"
        "                } else {\n"
        '                    android.util.Log.i("ReVanHide",\n'
        '                        "persist.sys.revan.mod=false → skipping hide logic");\n'
        "                }\n"
        "            } catch (Exception e) {\n"
        '                android.util.Log.w("ReVanHide", "Hide patch failed", e);\n'
        "            }\n"
        "            // --- END HIDE PATCH ---\n\n"
        "            return res;"
    )

    new_content = content[: m.start()] + m.group(1) + replacement_block + content[m.end() :]
    apm_path.write_text(new_content, encoding="utf-8")


def adapt_fwb_commit_2(fwb_dir: Path) -> None:
    """Structurally adapts commit 2a8351dd7fcd3e4300df10e793709939880284e8."""
    pis_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerService.java"
    content = pis_path.read_text(encoding="utf-8")

    content = ensure_java_import(content, "import android.os.SystemProperties;")

    # 1. createSessionInternal hook
    anchor_create = re.compile(
        r"(if\s*\(\s*params\.appPackageName\s*!=\s*null\s*&&\s*!isValidPackageName\(params\.appPackageName\)\s*\)\s*\{\s*"
        r"params\.appPackageName\s*=\s*null;\s*\})",
        flags=re.S,
    )
    m1 = anchor_create.search(content)
    if not m1:
        raise RuntimeError(
            "Incompatible PackageInstallerService.java: could not locate params.appPackageName validation in createSessionInternal."
        )

    create_block = (
        "\n\n        // revanced blocker\n"
        "        String trgtPkg = params.appPackageName;\n\n"
        "        // Only enforce if the prop is set to false\n"
        '        boolean blockrv = android.os.SystemProperties.getBoolean("persist.sys.revan.mod", true);\n\n'
        '        if (blockrv && trgtPkg != null && "com.android.vending".equals(installerPackageName)) {\n'
        '            if ("com.google.android.youtube".equals(trgtPkg)\n'
        '                    || "com.google.android.apps.youtube.music".equals(trgtPkg)) {\n'
        '                throw new SecurityException("Play Store updates blocked for " + trgtPkg);\n'
        "            }\n"
        "        }\n"
        "        // revanced blocker"
    )
    content = content[: m1.end()] + create_block + content[m1.end() :]

    # 2. installExistingPackage hook
    anchor_install = re.compile(
        r"(public\s+void\s+installExistingPackage\s*\(\s*String\s+packageName\s*,\s*int\s+installFlags\s*,\s*int\s+installReason\s*,\s*"
        r"IntentSender\s+statusReceiver\s*,\s*int\s+userId\s*,\s*List<String>\s+allowListedPermissions\s*\)\s*\{)",
        flags=re.S,
    )
    m2 = anchor_install.search(content)
    if not m2:
        raise RuntimeError(
            "Incompatible PackageInstallerService.java: could not locate installExistingPackage method signature."
        )

    install_block = (
        "\n\n        // revanced blocker\n"
        "        final int callingUid = Binder.getCallingUid();\n"
        "        final Computer snapshot = mPm.snapshotComputer();\n"
        "        boolean callerIsPlayStore = false;\n"
        "        try {\n"
        "            String[] pkgs = snapshot.getPackagesForUid(callingUid);\n"
        "            if (pkgs != null) {\n"
        "                for (String p : pkgs) {\n"
        '                    if ("com.android.vending".equals(p)) {\n'
        "                        callerIsPlayStore = true;\n"
        "                        break;\n"
        "                    }\n"
        "                }\n"
        "            }\n"
        "        } catch (Exception e) {\n"
        "            // Be defensive — if snapshot API changes, don't crash the installer.\n"
        '            Slog.w(TAG, "RevancedBlocker: error checking installer uid: " + e);\n'
        "        }\n\n"
        '        boolean allowUpdates = android.os.SystemProperties.getBoolean("persist.sys.revan.mod", true);\n'
        "        if (allowUpdates && callerIsPlayStore\n"
        '                && ("com.google.android.youtube".equals(packageName)\n'
        '                    || "com.google.android.apps.youtube.music".equals(packageName))) {\n'
        '            Slog.i(TAG, "RevancedBlocker: blocking installExistingPackage for " + packageName);\n'
        "            // Inform Play Store of a failed install and return early to avoid heavy IO.\n"
        "            InstallPackageHelper.onInstallComplete(PackageManager.INSTALL_FAILED_ABORTED, mContext, statusReceiver);\n"
        "            return;\n"
        "        }"
    )
    content = content[: m2.end()] + install_block + content[m2.end() :]
    pis_path.write_text(content, encoding="utf-8")


def adapt_fwb_commit_3(fwb_dir: Path) -> None:
    """Structurally adapts commit 5a97e2194499df3271770146168f75d81869241b."""
    apm_path = fwb_dir / "core/java/android/app/ApplicationPackageManager.java"
    pis_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerService.java"
    psess_path = fwb_dir / "services/core/java/com/android/server/pm/PackageInstallerSession.java"

    # --- 1. ApplicationPackageManager.java ---
    apm = apm_path.read_text(encoding="utf-8")
    apm = ensure_java_import(apm, "import android.annotation.Nullable;")
    apm = ensure_java_import(apm, "import android.os.SystemProperties;")

    if "PROPERTY_MANAGED_STORE_UPDATES" not in apm:
        m_tag = re.search(
            r"(private static final boolean DEBUG_ICONS = [^\n]+;\n|private static final String TAG = \"ApplicationPackageManager\";\n)",
            apm,
        )
        if not m_tag:
            raise RuntimeError("Incompatible ApplicationPackageManager.java: missing TAG / DEBUG_ICONS constant anchor.")
        consts = (
            '    private static final String PACKAGE_PLAY_STORE = "com.android.vending";\n'
            '    private static final String PACKAGE_YOUTUBE = "com.google.android.youtube";\n'
            '    private static final String PACKAGE_YOUTUBE_MUSIC = "com.google.android.apps.youtube.music";\n'
            '    private static final String PROPERTY_MANAGED_STORE_UPDATES = "persist.sys.revan.mod";\n'
        )
        apm = apm[: m_tag.end()] + consts + apm[m_tag.end() :]

    # Guard getPackageInfoAsUser
    m_pkg_info = re.search(
        r"(public\s+PackageInfo\s+getPackageInfoAsUser\s*\(\s*String\s+packageName\s*,\s*PackageInfoFlags\s+flags\s*,\s*int\s+userId\s*\)\s*throws\s+NameNotFoundException\s*\{\n)",
        apm,
    )
    if not m_pkg_info:
        raise RuntimeError("Incompatible ApplicationPackageManager.java: missing getPackageInfoAsUser(String, PackageInfoFlags, int).")
    if "shouldHideManagedPackage(packageName)" not in apm[m_pkg_info.end() : m_pkg_info.end() + 200]:
        guard = (
            "        if (shouldHideManagedPackage(packageName)) {\n"
            "            throw new NameNotFoundException(packageName);\n"
            "        }\n"
        )
        apm = apm[: m_pkg_info.end()] + guard + apm[m_pkg_info.end() :]

    # Guard getApplicationInfoAsUser
    m_app_info = re.search(
        r"(public\s+ApplicationInfo\s+getApplicationInfoAsUser\s*\(\s*String\s+packageName\s*,\s*ApplicationInfoFlags\s+flags\s*,\s*int\s+userId\s*\)\s*throws\s+NameNotFoundException\s*\{\n)",
        apm,
    )
    if not m_app_info:
        raise RuntimeError("Incompatible ApplicationPackageManager.java: missing getApplicationInfoAsUser(String, ApplicationInfoFlags, int).")
    if "shouldHideManagedPackage(packageName)" not in apm[m_app_info.end() : m_app_info.end() + 200]:
        guard = (
            "        if (shouldHideManagedPackage(packageName)) {\n"
            "            throw new NameNotFoundException(packageName);\n"
            "        }\n"
        )
        apm = apm[: m_app_info.end()] + guard + apm[m_app_info.end() :]

    # Helper methods in ApplicationPackageManager
    if "private boolean shouldHideManagedPackage(@Nullable String packageName)" not in apm:
        m_helper_anchor = re.search(
            r"(\n    @Override\n    public String getNameForUid\(int uid\))", apm
        )
        if not m_helper_anchor:
            raise RuntimeError("Incompatible ApplicationPackageManager.java: missing getNameForUid anchor.")
        helpers = (
            "\n    private boolean shouldHideManagedPackage(@Nullable String packageName) {\n"
            "        return shouldHideManagedPackages() && isManagedPackage(packageName);\n"
            "    }\n\n"
            "    private boolean shouldHideManagedPackages() {\n"
            "        return SystemProperties.getBoolean(PROPERTY_MANAGED_STORE_UPDATES, true)\n"
            "                && PACKAGE_PLAY_STORE.equals(mContext.getOpPackageName());\n"
            "    }\n\n"
            "    private static boolean isManagedPackage(@Nullable String packageName) {\n"
            "        return PACKAGE_YOUTUBE.equals(packageName) || PACKAGE_YOUTUBE_MUSIC.equals(packageName);\n"
            "    }\n"
        )
        apm = apm[: m_helper_anchor.start()] + helpers + apm[m_helper_anchor.start() :]

    # Replace ReVanHide block or plain return in getInstalledPackagesAsUser
    revan_hide_pat = re.compile(
        r"List<PackageInfo>\s+res\s*=\s*parceledList\.getList\(\);\s*"
        r"// --- BEGIN HIDE PATCH.*?// --- END HIDE PATCH ---\s*"
        r"return\s+res;",
        flags=re.S,
    )
    new_pkg_list_block = (
        "List<PackageInfo> res = parceledList.getList();\n"
        "            if (shouldHideManagedPackages()) {\n"
        "                res.removeIf(pi -> pi != null && isManagedPackage(pi.packageName));\n"
        "            }\n"
        "            return res;"
    )
    if revan_hide_pat.search(apm):
        apm = revan_hide_pat.sub(new_pkg_list_block, apm, count=1)
    elif "res.removeIf(pi -> pi != null && isManagedPackage(pi.packageName));" not in apm:
        raw_pkg_pat = re.compile(
            r"(public\s+List<PackageInfo>\s+getInstalledPackagesAsUser\s*\(\s*PackageInfoFlags\s+flags\s*,\s*int\s+userId\s*\)\s*\{.*?"
            r"if\s*\(\s*parceledList\s*==\s*null\s*\)\s*\{\s*return\s+Collections\.emptyList\(\);\s*\}\s*)"
            r"return\s+parceledList\.getList\(\);",
            flags=re.S,
        )
        m_raw_pkg = raw_pkg_pat.search(apm)
        if not m_raw_pkg:
            raise RuntimeError("Incompatible ApplicationPackageManager.java: missing getInstalledPackagesAsUser return site.")
        apm = apm[: m_raw_pkg.start()] + m_raw_pkg.group(1) + new_pkg_list_block + apm[m_raw_pkg.end() :]

    # Update getInstalledApplicationsAsUser
    if "res.removeIf(ai -> ai != null && isManagedPackage(ai.packageName));" not in apm:
        raw_app_pat = re.compile(
            r"(public\s+List<ApplicationInfo>\s+getInstalledApplicationsAsUser\s*\(\s*ApplicationInfoFlags\s+flags\s*,\s*int\s+userId\s*\)\s*\{.*?"
            r"if\s*\(\s*parceledList\s*==\s*null\s*\)\s*\{\s*return\s+Collections\.emptyList\(\);\s*\}\s*)"
            r"return\s+parceledList\.getList\(\);",
            flags=re.S,
        )
        m_raw_app = raw_app_pat.search(apm)
        if not m_raw_app:
            raise RuntimeError("Incompatible ApplicationPackageManager.java: missing getInstalledApplicationsAsUser return site.")
        new_app_list_block = (
            "List<ApplicationInfo> res = parceledList.getList();\n"
            "            if (shouldHideManagedPackages()) {\n"
            "                res.removeIf(ai -> ai != null && isManagedPackage(ai.packageName));\n"
            "            }\n"
            "            return res;"
        )
        apm = apm[: m_raw_app.start()] + m_raw_app.group(1) + new_app_list_block + apm[m_raw_app.end() :]

    # --- 2. PackageInstallerService.java ---
    pis = pis_path.read_text(encoding="utf-8")
    pis = ensure_java_import(pis, "import android.annotation.Nullable;")
    pis = ensure_java_import(pis, "import android.os.SystemProperties;")
    pis = ensure_java_import(pis, "import com.android.internal.util.ArrayUtils;")

    if "PROPERTY_MANAGED_STORE_UPDATES" not in pis:
        m_pis_tag = re.search(
            r"(private static final boolean LOGD = [^\n]+;\n|private static final String TAG = \"PackageInstaller\";\n)",
            pis,
        )
        if not m_pis_tag:
            raise RuntimeError("Incompatible PackageInstallerService.java: missing TAG / LOGD constant anchor.")
        consts = (
            '    private static final String PACKAGE_PLAY_STORE = "com.android.vending";\n'
            '    private static final String PACKAGE_YOUTUBE = "com.google.android.youtube";\n'
            '    private static final String PACKAGE_YOUTUBE_MUSIC = "com.google.android.apps.youtube.music";\n'
            '    private static final String PROPERTY_MANAGED_STORE_UPDATES = "persist.sys.revan.mod";\n'
        )
        pis = pis[: m_pis_tag.end()] + consts + pis[m_pis_tag.end() :]

    # Replace or insert createSessionInternal check
    legacy_create_pat = re.compile(
        r"// revanced blocker\s*String trgtPkg = params\.appPackageName;.*?// revanced blocker",
        flags=re.S,
    )
    new_create_check = (
        "if (shouldBlockManagedStoreUpdate(installerPackageName, params.appPackageName)) {\n"
        '            throw new SecurityException("Play Store updates blocked for " + params.appPackageName);\n'
        "        }"
    )
    if legacy_create_pat.search(pis):
        pis = legacy_create_pat.sub(new_create_check, pis, count=1)
    elif "shouldBlockManagedStoreUpdate(installerPackageName, params.appPackageName)" not in pis:
        anchor_create = re.compile(
            r"(if\s*\(\s*params\.appPackageName\s*!=\s*null\s*&&\s*!isValidPackageName\(params\.appPackageName\)\s*\)\s*\{\s*"
            r"params\.appPackageName\s*=\s*null;\s*\})",
            flags=re.S,
        )
        m_c = anchor_create.search(pis)
        if not m_c:
            raise RuntimeError("Incompatible PackageInstallerService.java: missing params.appPackageName validation anchor.")
        pis = pis[: m_c.end()] + "\n\n        " + new_create_check + pis[m_c.end() :]

    # Helper methods in PackageInstallerService
    if "static boolean shouldBlockManagedStoreUpdate(@Nullable String installerPackageName," not in pis:
        m_stage = re.search(
            r"(private String buildExternalStageCid\(int sessionId\)\s*\{\s*return\s+\"smdl\"\s*\+\s*sessionId\s*\+\s*\"\.tmp\";\s*\})",
            pis,
        )
        if not m_stage:
            raise RuntimeError("Incompatible PackageInstallerService.java: missing buildExternalStageCid anchor.")
        pis_helpers = (
            "\n\n    static boolean shouldBlockManagedStoreUpdate(@Nullable String installerPackageName,\n"
            "            @Nullable String packageName) {\n"
            "        return SystemProperties.getBoolean(PROPERTY_MANAGED_STORE_UPDATES, true)\n"
            "                && PACKAGE_PLAY_STORE.equals(installerPackageName)\n"
            "                && isManagedPackage(packageName);\n"
            "    }\n\n"
            "    private boolean shouldBlockManagedStoreUpdate(@Nullable String packageName, int callingUid) {\n"
            "        return SystemProperties.getBoolean(PROPERTY_MANAGED_STORE_UPDATES, true)\n"
            "                && isManagedPackage(packageName)\n"
            "                && ArrayUtils.contains(mPm.snapshotComputer().getPackagesForUid(callingUid),\n"
            "                        PACKAGE_PLAY_STORE);\n"
            "    }\n\n"
            "    private static boolean isManagedPackage(@Nullable String packageName) {\n"
            "        return PACKAGE_YOUTUBE.equals(packageName) || PACKAGE_YOUTUBE_MUSIC.equals(packageName);\n"
            "    }"
        )
        pis = pis[: m_stage.end()] + pis_helpers + pis[m_stage.end() :]

    # Replace or insert installExistingPackage check
    legacy_install_pat = re.compile(
        r"// revanced blocker\s*final int callingUid = Binder\.getCallingUid\(\);.*?InstallPackageHelper\.onInstallComplete\(PackageManager\.INSTALL_FAILED_ABORTED,\s*mContext,\s*statusReceiver\);\s*return;\s*\}",
        flags=re.S,
    )
    new_install_check = (
        "if (shouldBlockManagedStoreUpdate(packageName, Binder.getCallingUid())) {\n"
        "            InstallPackageHelper.onInstallComplete(PackageManager.INSTALL_FAILED_ABORTED,\n"
        "                    mContext, statusReceiver);\n"
        "            return;\n"
        "        }"
    )
    if legacy_install_pat.search(pis):
        pis = legacy_install_pat.sub(new_install_check, pis, count=1)
    elif "shouldBlockManagedStoreUpdate(packageName, Binder.getCallingUid())" not in pis:
        anchor_install = re.compile(
            r"(public\s+void\s+installExistingPackage\s*\(\s*String\s+packageName\s*,\s*int\s+installFlags\s*,\s*int\s+installReason\s*,\s*"
            r"IntentSender\s+statusReceiver\s*,\s*int\s+userId\s*,\s*List<String>\s+allowListedPermissions\s*\)\s*\{)",
            flags=re.S,
        )
        m_i = anchor_install.search(pis)
        if not m_i:
            raise RuntimeError("Incompatible PackageInstallerService.java: missing installExistingPackage signature.")
        pis = pis[: m_i.end()] + "\n\n        " + new_install_check + pis[m_i.end() :]

    # --- 3. PackageInstallerSession.java ---
    psess = psess_path.read_text(encoding="utf-8")
    psess = ensure_java_import(
        psess, "import static android.content.pm.PackageManager.INSTALL_FAILED_ABORTED;"
    )

    if "enforceManagedStoreUpdateBlock();" not in psess:
        verify_pat = re.compile(
            r"(for\s*\(\s*PackageInstallerSession\s+child\s*:\s*children\s*\)\s*\{\s*"
            r"child\.prepareInheritedFiles\(\);\s*"
            r"child\.parseApk\(\);)"
            r"(\s*\}\s*\}\s*else\s*\{\s*"
            r"prepareInheritedFiles\(\);\s*"
            r"parseApk\(\);)"
            r"(\s*\}\s*\}\s*catch\s*\(\s*PackageManagerException\s+e\s*\)\s*\{\s*"
            r"final\s+String\s+completeMsg\s*=\s*ExceptionUtils\.getCompleteMessage\(e\);\s*"
            r"final\s+String\s+errorMsg\s*=\s*PackageManager\.installStatusToString\(e\.error,\s*completeMsg\);\s*"
            r"setSessionFailed\(e\.error,\s*errorMsg\);\s*"
            r"onSessionVerificationFailure\(e\.error,\s*errorMsg,\s*/\*\s*extras=\s*\*/\s*null\);)",
            flags=re.S,
        )
        m_v = verify_pat.search(psess)
        if not m_v:
            raise RuntimeError(
                "Incompatible PackageInstallerSession.java: could not locate parseApk() / onSessionVerificationFailure() block."
            )
        replaced_verify = (
            m_v.group(1)
            + "\n                    child.enforceManagedStoreUpdateBlock();"
            + m_v.group(2)
            + "\n                enforceManagedStoreUpdateBlock();"
            + m_v.group(3)
            + "\n            if (e.error == INSTALL_FAILED_ABORTED) {\n"
            + "                return;\n"
            + "            }"
        )
        psess = psess[: m_v.start()] + replaced_verify + psess[m_v.end() :]

    if "private void enforceManagedStoreUpdateBlock()" not in psess:
        m_after_verify = re.search(
            r"(\n    private boolean isVerificationServiceEnabled\(\))", psess
        )
        if not m_after_verify:
            raise RuntimeError(
                "Incompatible PackageInstallerSession.java: missing isVerificationServiceEnabled() anchor."
            )
        enforce_method = (
            "\n    private void enforceManagedStoreUpdateBlock() throws PackageManagerException {\n"
            "        if (PackageInstallerService.shouldBlockManagedStoreUpdate(getInstallerPackageName(),\n"
            "                getPackageName())) {\n"
            "            throw new PackageManagerException(INSTALL_FAILED_ABORTED,\n"
            '                    "Play Store updates blocked for " + getPackageName());\n'
            "        }\n"
            "    }\n"
        )
        psess = psess[: m_after_verify.start()] + enforce_method + psess[m_after_verify.start() :]

    # Write all 3 files after all checks succeeded
    apm_path.write_text(apm, encoding="utf-8")
    pis_path.write_text(pis, encoding="utf-8")
    psess_path.write_text(psess, encoding="utf-8")


def adapt_settings_commit_4(settings_dir: Path) -> None:
    """Structurally adapts commit 853d6a2aa1a7f68777679e4725a5f5a010bf37c7."""
    apps_xml_path = settings_dir / "res/xml/apps.xml"
    frag_path = settings_dir / "src/com/android/settings/applications/AppDashboardFragment.java"
    rev_strings_path = settings_dir / "res/values/revanced_strings.xml"

    if not apps_xml_path.is_file():
        raise RuntimeError(f"Incompatible Settings tree: missing {apps_xml_path}")
    if not frag_path.is_file():
        raise RuntimeError(f"Incompatible Settings tree: missing {frag_path}")

    # 1. Ensure all 5 revan_* strings exist without duplicating any existing definitions
    occ = find_settings_string_occurrences(settings_dir)
    existing_files = {f for files in occ.values() for f in files}
    missing_keys = [k for k, files in occ.items() if len(files) == 0]

    if missing_keys:
        if len(existing_files) == 1:
            target_str_file = next(iter(existing_files))
            text = target_str_file.read_text(encoding="utf-8")
            if "</resources>" not in text:
                raise RuntimeError(f"Invalid XML resources file: {target_str_file}")
            add_lines = "\n".join(
                f'    <string name="{k}">{REQUIRED_SETTINGS_STRINGS[k]}</string>'
                for k in missing_keys
            )
            text = text.replace("</resources>", f"{add_lines}\n</resources>", 1)
            target_str_file.write_text(text, encoding="utf-8")
        else:
            rev_strings_content = (
                '<?xml version="1.0" encoding="utf-8"?>\n'
                "<!--\n"
                "     SPDX-FileCopyrightText: 2026 LumineDroid\n"
                "     SPDX-License-Identifier: Apache-2.0\n"
                "-->\n"
                '<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">\n'
                "    <!-- ReVanced -->\n"
                + "\n".join(
                    f'    <string name="{k}">{REQUIRED_SETTINGS_STRINGS[k]}</string>'
                    for k in missing_keys
                )
                + "\n</resources>\n"
            )
            rev_strings_path.write_text(rev_strings_content, encoding="utf-8")

    # 2. Ensure SwitchPreferenceCompat is in res/xml/apps.xml
    apps_xml = apps_xml_path.read_text(encoding="utf-8")
    if 'android:key="persist_revan_mod"' not in apps_xml:
        switch_snippet = (
            "    <SwitchPreferenceCompat\n"
            '        android:key="persist_revan_mod"\n'
            '        android:title="@string/revan_toggle_title"\n'
            '        android:summary="@string/revan_toggle_summary"\n'
            '        android:order="-993"\n'
            '        android:defaultValue="true" />\n\n'
        )
        m_placeholder = re.search(
            r"([ \t]*<PreferenceCategory\s+[^>]*android:key=\"dashboard_tile_placeholder\")",
            apps_xml,
        )
        if m_placeholder:
            apps_xml = (
                apps_xml[: m_placeholder.start()]
                + switch_snippet
                + apps_xml[m_placeholder.start() :]
            )
        elif "</PreferenceScreen>" in apps_xml:
            apps_xml = apps_xml.replace(
                "</PreferenceScreen>", switch_snippet + "</PreferenceScreen>", 1
            )
        else:
            raise RuntimeError(
                "Incompatible res/xml/apps.xml: could not find dashboard_tile_placeholder or </PreferenceScreen>."
            )
        apps_xml_path.write_text(apps_xml, encoding="utf-8")

    # 3. Adapt AppDashboardFragment.java
    frag = frag_path.read_text(encoding="utf-8")
    required_imports = [
        "import android.content.pm.IPackageDeleteObserver;",
        "import android.content.pm.PackageManager;",
        "import android.os.PowerManager;",
        "import android.os.SystemProperties;",
        "import androidx.appcompat.app.AlertDialog;",
        "import androidx.preference.Preference;",
        "import androidx.preference.SwitchPreferenceCompat;",
        "import static android.os.UserHandle.USER_SYSTEM;",
        "import java.util.concurrent.atomic.AtomicInteger;",
    ]
    for imp in required_imports:
        frag = ensure_java_import(frag, imp)

    # Ensure constants
    if "REVAN_PREF_KEY" not in frag:
        m_const_anchor = re.search(
            r"(private static final String ASPECT_RATIO_PREF_KEY = [^\n]+;\n|private static final String TAG = \"AppDashboardFragment\";\n)",
            frag,
        )
        if not m_const_anchor:
            raise RuntimeError("Incompatible AppDashboardFragment.java: missing constant anchor.")
        consts = (
            '    private static final String REVAN_PREF_KEY = "persist_revan_mod";\n'
            '    private static final String REVAN_PROP = "persist.sys.revan.mod";\n'
            "    private static final String[] REVAN_PACKAGES = {\n"
            '            "com.google.android.youtube",\n'
            '            "com.google.android.apps.youtube.music"\n'
            "    };\n"
        )
        frag = frag[: m_const_anchor.end()] + consts + frag[m_const_anchor.end() :]

    # Remove older partial ReVanced methods if upgrading from an earlier revision
    frag = re.sub(
        r"\n    @Override\n    public void onStart\(\)\s*\{\s*super\.onStart\(\);\s*final Preference pref = findPreference\((?:REVAN_PREF_KEY|\"persist_revan_mod\")\);.*?\n    \}\n",
        "\n",
        frag,
        flags=re.S,
    )
    frag = re.sub(
        r"\n    private void showRevanRestartDialog\(SwitchPreferenceCompat toggle, boolean enabled\)\s*\{.*?\n    \}\n",
        "\n",
        frag,
        flags=re.S,
    )

    revan_methods = (
        "\n    private void showRevanRestartDialog(SwitchPreferenceCompat toggle, boolean enabled) {\n"
        "        new AlertDialog.Builder(getContext())\n"
        "                .setTitle(R.string.revan_restart_dialog_title)\n"
        "                .setMessage(R.string.revan_restart_dialog_message)\n"
        "                .setPositiveButton(R.string.revan_restart_now, (dialog, which) -> {\n"
        "                    final Context context = requireContext().getApplicationContext();\n"
        "                    toggle.setChecked(enabled);\n"
        "                    if (enabled) {\n"
        "                        uninstallUpdatesThenEnable(context);\n"
        "                    } else {\n"
        '                        SystemProperties.set(REVAN_PROP, "false");\n'
        "                        reboot(context);\n"
        "                    }\n"
        "                })\n"
        "                .setNegativeButton(android.R.string.cancel, null)\n"
        "                .show();\n"
        "    }\n\n"
        "    private void uninstallUpdatesThenEnable(Context context) {\n"
        "        // Keep the property false while PackageManager restores stock system package paths.\n"
        "        final PackageManager pm = context.getPackageManager();\n"
        "        final AtomicInteger pendingDeletes = new AtomicInteger(REVAN_PACKAGES.length);\n"
        "        final IPackageDeleteObserver observer = new IPackageDeleteObserver.Stub() {\n"
        "            @Override\n"
        "            public void packageDeleted(String packageName, int returnCode) {\n"
        "                if (pendingDeletes.decrementAndGet() == 0) {\n"
        '                    SystemProperties.set(REVAN_PROP, "true");\n'
        "                    reboot(context);\n"
        "                }\n"
        "            }\n"
        "        };\n\n"
        "        for (String pkg : REVAN_PACKAGES) {\n"
        "            pm.deletePackageAsUser(pkg, observer, 0, USER_SYSTEM);\n"
        "        }\n"
        "    }\n\n"
        "    private void reboot(Context context) {\n"
        "        context.getSystemService(PowerManager.class).reboot(null);\n"
        "    }\n"
    )

    onstart_pref_hook = (
        "\n        final Preference pref = findPreference(REVAN_PREF_KEY);\n"
        "        if (pref instanceof SwitchPreferenceCompat) {\n"
        "            final SwitchPreferenceCompat toggle = (SwitchPreferenceCompat) pref;\n"
        "            toggle.setChecked(SystemProperties.getBoolean(REVAN_PROP, true));\n"
        "            toggle.setOnPreferenceChangeListener((p, newVal) -> {\n"
        "                showRevanRestartDialog(toggle, (Boolean) newVal);\n"
        "                return false;\n"
        "            });\n"
        "        }\n"
    )

    if "public void onStart()" in frag:
        # Target ROM already has an unrelated onStart() method: preserve it and hook after super.onStart()
        if "findPreference(REVAN_PREF_KEY)" not in frag:
            m_super = re.search(r"(public\s+void\s+onStart\s*\(\s*\)\s*\{\s*super\.onStart\(\);)", frag)
            if not m_super:
                raise RuntimeError("Incompatible AppDashboardFragment.java: existing onStart() has no super.onStart().")
            frag = frag[: m_super.end()] + onstart_pref_hook + frag[m_super.end() :]
        if "private void uninstallUpdatesThenEnable(Context context)" not in frag:
            m_vis = re.search(
                r"(\n    @VisibleForTesting\n    PreferenceCategoryController getAdvancedAppsPreferenceCategoryController|\n    @Override\n    protected List<AbstractPreferenceController> createPreferenceControllers)",
                frag,
            )
            if not m_vis:
                raise RuntimeError("Incompatible AppDashboardFragment.java: could not find method insertion anchor.")
            frag = frag[: m_vis.start()] + revan_methods + frag[m_vis.start() :]
    else:
        full_block = (
            "\n    @Override\n"
            "    public void onStart() {\n"
            "        super.onStart();\n"
            + onstart_pref_hook
            + "    }\n"
            + revan_methods
        )
        m_vis = re.search(
            r"(\n    @VisibleForTesting\n    PreferenceCategoryController getAdvancedAppsPreferenceCategoryController|\n    @Override\n    protected List<AbstractPreferenceController> createPreferenceControllers)",
            frag,
        )
        if not m_vis:
            raise RuntimeError("Incompatible AppDashboardFragment.java: could not find method insertion anchor.")
        frag = frag[: m_vis.start()] + full_block + frag[m_vis.start() :]

    frag_path.write_text(frag, encoding="utf-8")


# ---------------------------------------------------------------------------
# Commit Application Orchestrator
# ---------------------------------------------------------------------------

def apply_or_adapt_commit(
    repo_dir: Path,
    revanced_dir: Path,
    spec: Dict[str, object],
    verify_fn,
    adapt_fn,
    no_commit: bool = False,
    quiet: bool = False,
) -> Dict[str, object]:
    commit_id = str(spec["id"])
    orig_sha = str(spec["sha"])
    subject = str(spec["subject"])
    rel_files = list(spec["files"])
    patch_path = revanced_dir / str(spec["patch_file"])

    # 1. Check if already satisfied in code
    ok_code, code_issues = verify_fn(repo_dir)
    hist_sha = check_commit_in_history(repo_dir, spec)
    if ok_code:
        log_ok(
            f"{spec['prompt_label']} ({orig_sha[:12]} '{subject}'): "
            f"ALREADY_SATISFIED (history={hist_sha[:12] if hist_sha else 'worktree'}, code verified)",
            quiet,
        )
        return {
            "id": commit_id,
            "original_sha": orig_sha,
            "subject": subject,
            "status": "ALREADY_SATISFIED",
            "method": "verified_existing",
            "applied_sha": hist_sha,
        }

    # 2. Check for conflicting uncommitted changes on target files
    dirty_targets = get_dirty_files_for_paths(repo_dir, rel_files)
    if dirty_targets:
        raise RuntimeError(
            f"Refusing to overwrite uncommitted changes in {repo_dir} for {orig_sha[:12]}:\n  "
            + "\n  ".join(dirty_targets)
        )

    # Check if index has staged changes from unrelated work
    staged_res = run_cmd(["git", "diff", "--cached", "--name-only"], cwd=repo_dir)
    has_unrelated_staged = bool(staged_res.stdout.strip())

    method_used = None

    # 3. Try direct patch application first (only if no duplicate string conflict in Settings)
    can_use_raw_patch = patch_path.is_file()
    if commit_id == "settings_commit_4_toggle":
        occ = find_settings_string_occurrences(repo_dir)
        if any(len(files) > 0 for files in occ.values()):
            # Strings already exist in another file (e.g. lumine_strings.xml); use structural adapter
            can_use_raw_patch = False

    if can_use_raw_patch:
        chk = run_cmd(["git", "apply", "--check", str(patch_path)], cwd=repo_dir, check=False)
        if chk.returncode == 0:
            log_info(f"Applying exact patch for {orig_sha[:12]} ({subject})...", quiet)
            run_cmd(["git", "apply", str(patch_path)], cwd=repo_dir, check=True)
            method_used = "exact_patch"

    # 4. Fallback to structural ROM-aware adaptation
    if method_used is None:
        log_info(
            f"Patch context differs on target ROM for {orig_sha[:12]} ({subject}); "
            "running structural source adapter...",
            quiet,
        )
        try:
            adapt_fn(repo_dir)
        except Exception:
            for rel_f in rel_files:
                run_cmd(["git", "checkout", "--", rel_f], cwd=repo_dir, check=False)
                full_f = repo_dir / rel_f
                if rel_f == "res/values/revanced_strings.xml" and full_f.is_file():
                    full_f.unlink()
            raise
        method_used = "structural_adaptation"

    # 5. Verify resulting code before committing
    ok_after, after_issues = verify_fn(repo_dir)
    if not ok_after:
        # Roll back target files on verification failure so repository is never left broken
        for rel_f in rel_files:
            run_cmd(["git", "checkout", "--", rel_f], cwd=repo_dir, check=False)
            full_f = repo_dir / rel_f
            if rel_f == "res/values/revanced_strings.xml" and full_f.is_file():
                full_f.unlink()
        raise RuntimeError(
            f"Post-adaptation verification failed for {orig_sha[:12]} ({subject}):\n  - "
            + "\n  - ".join(after_issues)
        )

    applied_sha = None
    if not no_commit and not has_unrelated_staged:
        existing_files = [f for f in rel_files if (repo_dir / f).is_file()]
        run_cmd(["git", "add", "--"] + existing_files, cwd=repo_dir, check=True)
        env = {
            "GIT_AUTHOR_NAME": "Quick ⚡",
            "GIT_AUTHOR_EMAIL": "quick@disroot.org",
            "GIT_AUTHOR_DATE": str(spec["date"]),
            "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", "ReVanced Integration"),
            "GIT_COMMITTER_EMAIL": os.environ.get("GIT_COMMITTER_EMAIL", "revanced@localhost"),
        }
        run_cmd(
            ["git", "commit", "-m", str(spec["message"])],
            cwd=repo_dir,
            check=True,
            env=env,
        )
        applied_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()

    log_ok(
        f"{spec['prompt_label']} ({orig_sha[:12]} '{subject}'): "
        f"INTEGRATED via {method_used}"
        + (f" -> commit {applied_sha[:12]}" if applied_sha else " (worktree)"),
        quiet,
    )
    return {
        "id": commit_id,
        "original_sha": orig_sha,
        "subject": subject,
        "status": "INTEGRATED",
        "method": method_used,
        "applied_sha": applied_sha,
    }


# ---------------------------------------------------------------------------
# Main Integration Flow
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automate and verify vendor/revanced ROM integration."
    )
    parser.add_argument("--root", type=Path, default=None, help="Android ROM tree root")
    parser.add_argument("--fwb-dir", type=Path, default=None, help="Override frameworks/base path")
    parser.add_argument(
        "--settings-dir", type=Path, default=None, help="Override packages/apps/Settings path"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read-only check mode (do not modify repositories or files)",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Apply changes to working tree without creating git commits",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output unless changes are applied or errors occur",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help="Write JSON verification report to the given path",
    )
    args = parser.parse_args()

    revanced_dir = Path(__file__).resolve().parent.parent
    root_dir = args.root.resolve() if args.root else find_tree_root(revanced_dir)
    if not root_dir:
        log_err("Could not locate Android source tree root (build/envsetup.sh not found).")
        return 1

    fwb_dir = args.fwb_dir.resolve() if args.fwb_dir else (root_dir / "frameworks" / "base")
    settings_dir = (
        args.settings_dir.resolve()
        if args.settings_dir
        else (root_dir / "packages" / "apps" / "Settings")
    )
    apply_mode = not args.check

    rom_meta = detect_rom_metadata(root_dir)
    log_info(
        f"ROM root: {root_dir} (detected={rom_meta.get('rom_name')}, "
        f"branch={rom_meta.get('rom_branch')})",
        args.quiet,
    )

    # 1. Verify / prepare prebuilt APKs & native libraries in vendor/revanced
    prebuilts_ok, prebuilt_errors = verify_and_prepare_prebuilts(
        revanced_dir, apply_mode=apply_mode, quiet=args.quiet
    )
    if not prebuilts_ok:
        for err in prebuilt_errors:
            log_err(err)
        return 1
    log_ok("vendor/revanced prebuilt APKs, arm64 native libraries, init.rv.rc, and sepolicy verified.", args.quiet)

    # 2. Inspect target git repositories
    try:
        fwb_git = inspect_git_repo(fwb_dir)
        settings_git = inspect_git_repo(settings_dir)
    except Exception as e:
        log_err(str(e))
        return 1

    log_info(
        f"frameworks/base: branch={fwb_git['branch'] or 'DETACHED'} "
        f"head={str(fwb_git['head_sha'])[:12]} dirty_tracked={len(fwb_git['dirty_tracked'])}",
        args.quiet,
    )
    log_info(
        f"packages/apps/Settings: branch={settings_git['branch'] or 'DETACHED'} "
        f"head={str(settings_git['head_sha'])[:12]} dirty_tracked={len(settings_git['dirty_tracked'])}",
        args.quiet,
    )

    commit_results: List[Dict[str, object]] = []
    fwb_verifiers = [
        (FWB_COMMITS[0], verify_fwb_commit_1_initial, adapt_fwb_commit_1),
        (FWB_COMMITS[1], verify_fwb_commit_2_fixup, adapt_fwb_commit_2),
        (FWB_COMMITS[2], verify_fwb_commit_3_harden, adapt_fwb_commit_3),
    ]

    if args.check:
        # Read-only verification mode
        all_ok = True
        for spec, verify_fn, _ in fwb_verifiers:
            ok, issues = verify_fn(fwb_dir)
            hist_sha = check_commit_in_history(fwb_dir, spec)
            status = "ALREADY_SATISFIED" if ok else "MISSING"
            commit_results.append(
                {
                    "id": spec["id"],
                    "original_sha": spec["sha"],
                    "subject": spec["subject"],
                    "status": status,
                    "history_sha": hist_sha,
                    "issues": issues,
                }
            )
            if ok:
                log_ok(f"{spec['prompt_label']} ({spec['sha'][:12]}): SATISFIED", args.quiet)
            else:
                all_ok = False
                log_err(f"{spec['prompt_label']} ({spec['sha'][:12]}): MISSING ({'; '.join(issues)})")

        ok_s, issues_s = verify_settings_commit_4(settings_dir)
        hist_s = check_commit_in_history(settings_dir, SETTINGS_COMMIT)
        commit_results.append(
            {
                "id": SETTINGS_COMMIT["id"],
                "original_sha": SETTINGS_COMMIT["sha"],
                "subject": SETTINGS_COMMIT["subject"],
                "status": "ALREADY_SATISFIED" if ok_s else "MISSING",
                "history_sha": hist_s,
                "issues": issues_s,
            }
        )
        if ok_s:
            log_ok(f"{SETTINGS_COMMIT['prompt_label']} ({SETTINGS_COMMIT['sha'][:12]}): SATISFIED", args.quiet)
        else:
            all_ok = False
            log_err(f"{SETTINGS_COMMIT['prompt_label']} ({SETTINGS_COMMIT['sha'][:12]}): MISSING ({'; '.join(issues_s)})")

        if args.json_report:
            write_if_changed(
                args.json_report,
                json.dumps(
                    {
                        "rom": rom_meta,
                        "prebuilts_ok": prebuilts_ok,
                        "frameworks_base": fwb_git,
                        "settings": settings_git,
                        "commits": commit_results,
                        "all_satisfied": all_ok,
                    },
                    indent=2,
                )
                + "\n",
            )
        return 0 if all_ok else 1

    # Apply / Adapt mode
    orig_fwb_head = str(fwb_git["head_sha"])
    fwb_had_dirty_tracked = bool(fwb_git["dirty_tracked"])
    try:
        for spec, verify_fn, adapt_fn in fwb_verifiers:
            res = apply_or_adapt_commit(
                fwb_dir,
                revanced_dir,
                spec,
                verify_fn,
                adapt_fn,
                no_commit=args.no_commit,
                quiet=args.quiet,
            )
            commit_results.append(res)
    except Exception as e:
        if not args.no_commit and not fwb_had_dirty_tracked:
            cur_fwb_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=fwb_dir).stdout.strip()
            if cur_fwb_head != orig_fwb_head:
                log_warn(
                    f"Rolling back partial frameworks/base commits to {orig_fwb_head[:12]}..."
                )
                run_cmd(["git", "reset", "--hard", orig_fwb_head], cwd=fwb_dir, check=False)
        log_err(f"Integration aborted safely: {e}")
        return 1

    try:
        res_s = apply_or_adapt_commit(
            settings_dir,
            revanced_dir,
            SETTINGS_COMMIT,
            verify_settings_commit_4,
            adapt_settings_commit_4,
            no_commit=args.no_commit,
            quiet=args.quiet,
        )
        commit_results.append(res_s)
    except Exception as e:
        log_err(f"Integration aborted safely: {e}")
        return 1

    # Final verification of both repositories
    final_fwb_ok, final_fwb_issues = verify_fwb_commit_3_harden(fwb_dir)
    final_set_ok, final_set_issues = verify_settings_commit_4(settings_dir)
    if not final_fwb_ok or not final_set_ok:
        for issue in final_fwb_issues + final_set_issues:
            log_err(f"Final verification error: {issue}")
        return 1

    # Record prepared state for build-time makefile verification (only when running on real tree)
    if fwb_dir == (root_dir / "frameworks" / "base") and settings_dir == (
        root_dir / "packages" / "apps" / "Settings"
    ):
        prepared_mk = revanced_dir / "common" / "prepared.mk"
        mk_content = (
            "# Auto-generated by vendor/revanced/apply.sh. Do not edit manually.\n"
            "REVANCED_SOURCE_PREPARED := true\n"
            "REVANCED_FWB_PREPARED := true\n"
            "REVANCED_SETTINGS_PREPARED := true\n"
        )
        write_if_changed(prepared_mk, mk_content)

        status_path = args.json_report or (revanced_dir / "common" / ".revanced_status.json")
        fwb_git_after = inspect_git_repo(fwb_dir)
        settings_git_after = inspect_git_repo(settings_dir)
        write_if_changed(
            status_path,
            json.dumps(
                {
                    "rom": rom_meta,
                    "prebuilts_ok": True,
                    "frameworks_base": fwb_git_after,
                    "settings": settings_git_after,
                    "commits": commit_results,
                    "all_satisfied": True,
                },
                indent=2,
            )
            + "\n",
        )

    if args.quiet:
        changed = [c for c in commit_results if c["status"] == "INTEGRATED"]
        if changed:
            print(
                f"[revanced] Integrated {len(changed)} commit(s): "
                + ", ".join(f"{c['original_sha'][:12]}" for c in changed)
            )
        else:
            print("[revanced] Integration verified (all 4 commits & prebuilts ready).")

    return 0


if __name__ == "__main__":
    sys.exit(main())

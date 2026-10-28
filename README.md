# ReVanced ROM Integration (`vendor/revanced`)

Self-contained Android ROM integration for ReVanced **YouTube** (`com.google.android.youtube`) and **YT Music** (`com.google.android.apps.youtube.music`), including:

- Release-key-signable presigned stock APKs (`YouTube`, `YTMusic`) and extracted `arm64` native libraries (`YouTube_libdir`, `YTMusic_libdir`).
- Patched ReVanced payloads (`YouTube_patched`, `YTMusic_patched`, installed as `.rv` bind-mount sources under `/product/etc/rv/` so `sign_target_files_apks` leaves their signatures untouched).
- `init` bind-mount configuration (`common/product/etc/init/init.rv.rc`) gated on `sys.boot_completed=1 && persist.sys.revan.mod=true` and private SELinux policy (`sepolicy/private/revanced_init.te`).
- Automated, idempotent `frameworks/base` and `packages/apps/Settings` patch/adaptation engine (`apply.sh`, `vendorsetup.sh`, `tools/revanced_integrate.py`, and `patches/`).

---

## Quick Start (Device Maintainer Workflow)

### 1. Provision `vendor/revanced`

Via local manifest (`.repo/local_manifests/revanced.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project path="vendor/revanced" name="Inventor365/vendor_revanced" remote="github" revision="penguin-clo-17" />
</manifest>
```

Or via `git clone` (with Git LFS enabled):

```bash
git clone -b penguin-clo-17 https://github.com/Inventor365/vendor_revanced.git vendor/revanced
```

### 2. Inherit in `device.mk`

Add the product makefile to your device's `device.mk`:

```makefile
$(call inherit-product, vendor/revanced/revanced.mk)
```

*(For backward compatibility with existing device trees, `$(call inherit-product, vendor/revanced/products/revanced.mk)` is also supported and delegates to `vendor/revanced/revanced.mk`.)*

### 3. Build the ROM

Source the build environment as usual:

```bash
source build/envsetup.sh
lunch <product>-<release>-<variant>
```

When `build/envsetup.sh` or `lunch` runs, `vendor/revanced/vendorsetup.sh` automatically invokes `bash vendor/revanced/apply.sh --auto` whenever a device in the workspace inherits `vendor/revanced/revanced.mk`.

You can also run the source-setup script explicitly at any time (for example, in CI or right after `repo sync`):

```bash
# Verify and apply/adapt any missing framework or Settings patches:
bash vendor/revanced/apply.sh

# Read-only verification check (no repository modifications):
bash vendor/revanced/apply.sh --check
```

---

## Architecture: Source-Setup vs. Build-Time Evaluation

Android product makefiles (`device.mk`, `revanced.mk`) are evaluated by `mk2rbc` / Starlark and `ckati` during product configuration. Mutating Git repositories or running network operations inside `.mk` files is unsafe and blocked by Soong's hermetic build sandbox (`path_interposer`).

This repository cleanly separates **source preparation** from **build-time evaluation**:

1. **Idempotent Source-Setup Stage (`vendorsetup.sh` -> `apply.sh` -> `tools/revanced_integrate.py`)**:
   - Runs automatically during `source build/envsetup.sh` / `lunch` (or manually via `bash vendor/revanced/apply.sh`).
   - Verifies that `YouTube.apk`, `YouTube_patched.apk`, `YTMusic.apk`, and `YTMusic_patched.apk` are valid ZIP/APK binaries (automatically running `git lfs pull` if Git LFS pointer files are detected).
   - Verifies that `arm64` native libraries (`common/product/app/{YouTube,YTMusic}/lib/arm64/*.so`) and `placeholder.txt` are extracted (automatically running `extract-libs.sh` if missing).
   - Inspects `frameworks/base` and `packages/apps/Settings` (`git status`, active branch, `HEAD`, remotes) and verifies whether all four required commits are present in the actual source code.
   - If any commit is missing, applies the exact patch (`patches/`) or runs the ROM-aware structural source adapter when surrounding ROM lines differ, validates all resulting symbols/imports/XML/braces, and writes `common/prepared.mk`.
   - Never overwrites uncommitted changes in target files, never resets branches, and rolls back cleanly if an incompatible Android revision is encountered.

2. **Hermetic Build-Time Assertions (`revanced.mk` & `common/Android.mk`)**:
   - Guarded by `REVANCED_PRODUCT_INCLUDED` / `REVANCED_COMMON_VENDOR_INCLUDED` / `REVANCED_ANDROID_MK_INCLUDED` so multiple inclusions never duplicate modules or properties.
   - `revanced.mk` (100% `mk2rbc` Starlark compatible) asserts that all prebuilt APKs, native library placeholders, `init.rv.rc`, `revanced_init.te`, target source files, and `REVANCED_SOURCE_PREPARED` are present; otherwise it halts product configuration with an actionable `$(error ...)` message instructing the user to run `bash vendor/revanced/apply.sh`.
   - `common/Android.mk` enforces that `arm64` is supported by `TARGET_ARCH` / `TARGET_2ND_ARCH`.

---

## Required Framework & Settings Commits

The integration manages and verifies four commits in dependency order:

| Order | Repository | Original Commit SHA | Subject | Files Touched |
|---|---|---|---|---|
| 1 | `frameworks/base` | `1531342eb63352c7a616cc8c83a2c8edec2c4723` | `base: Disable auto-updates for ReVanced Apps [1/2]` | `core/java/android/app/ApplicationPackageManager.java` |
| 2 | `frameworks/base` | `2a8351dd7fcd3e4300df10e793709939880284e8` | `fixup! base: Disable auto-updates for ReVanced Apps [1/2]` | `services/core/java/com/android/server/pm/PackageInstallerService.java` |
| 3 | `frameworks/base` | `5a97e2194499df3271770146168f75d81869241b` | `base: Harden Revanced update blocking` | `core/java/android/app/ApplicationPackageManager.java`<br>`services/core/java/com/android/server/pm/PackageInstallerService.java`<br>`services/core/java/com/android/server/pm/PackageInstallerSession.java` |
| 4 | `packages/apps/Settings` | `853d6a2aa1a7f68777679e4725a5f5a010bf37c7` | `Settings: Allow disabling ReVanced mods` | `res/values/revanced_strings.xml`<br>`res/xml/apps.xml`<br>`src/com/android/settings/applications/AppDashboardFragment.java` |

### Why Dependency Ordering Matters

- Commit `1531342eb633` introduces the initial Play Store package list filter in `ApplicationPackageManager.getInstalledPackagesAsUser`.
- Commit `2a8351dd7fcd` adds `SystemProperties` import and initial Play Store update blocking in `PackageInstallerService.createSessionInternal` and `installExistingPackage`.
- Commit `5a97e2194499` refactors and replaces the intermediate blocks from both `1531342eb633` and `2a8351dd7fcd` with log-neutral `shouldHideManagedPackage` / `shouldHideManagedPackages` / `shouldBlockManagedStoreUpdate` / `enforceManagedStoreUpdateBlock` helpers across `ApplicationPackageManager`, `PackageInstallerService`, and `PackageInstallerSession` (blocking direct `getPackageInfoAsUser` / `getApplicationInfoAsUser` queries, list queries, and post-`parseApk()` session verification).
- Commit `853d6a2aa1a7` adds the **ReVanced Integration** toggle (`persist_revan_mod` -> `persist.sys.revan.mod`) in **Settings -> Apps**, uninstalling Play Store updates via `IPackageDeleteObserver` before re-enabling and rebooting so `init.rv.rc` bind-mounts the ReVanced APKs cleanly over the stock presigned APKs.

---

## Supported ROMs & Compatibility Requirements

- **Primary verified target**: **PenguinOS `celerity`** (Android 17, CLO `LA.QSSI.17.0`, AOSPA `calcite` base, SDK 37).
- **Also compatible with**: Android 15 / 16 / 17 AOSP-derived ROMs (AOSPA, LineageOS, Lunaris/LumineDroid, PixelLineage, etc.) whose `ApplicationPackageManager`, `PackageInstallerService`, `PackageInstallerSession`, and `AppDashboardFragment` expose the standard AOSP `PackageInfoFlags`, `Computer`, `parseApk()`, and `DashboardFragment` APIs.
- **ROM-specific structural adaptation**:
  - If `res/xml/apps.xml` does not contain PenguinOS's `app_lock_settings` entry above `dashboard_tile_placeholder`, the structural adapter locates `dashboard_tile_placeholder` (or `</PreferenceScreen>`) directly.
  - If `revan_toggle_title` is already defined in another `res/values/*.xml` file (such as `lumine_strings.xml` on Lunaris), missing strings are added without creating duplicate resource definitions.
  - If `AppDashboardFragment.java` already defines a custom `onStart()`, the adapter hooks `findPreference(REVAN_PREF_KEY)` after `super.onStart()` while preserving the ROM's existing `onStart()` logic.
  - If a target tree lacks the required method signatures or APIs, `apply.sh` aborts safely with an explicit diagnostic and rolls back any partial changes.

---

## Updating Prebuilt APKs

1. Build or obtain the stock and patched ReVanced APKs (e.g. via [j-hc/revanced-magisk-module](https://github.com/j-hc/revanced-magisk-module)):
   - Stock YouTube (`com.google.android.youtube`): `common/product/app/YouTube/YouTube.apk`
   - Patched YouTube: `common/product/etc/rv/YouTube_patched.apk`
   - Stock YT Music (`com.google.android.apps.youtube.music`): `common/product/app/YTMusic/YTMusic.apk`
   - Patched YT Music: `common/product/etc/rv/YTMusic_patched.apk`
2. Extract the `arm64` native libraries:
   ```bash
   bash vendor/revanced/extract-libs.sh
   ```
3. Run verification:
   ```bash
   bash vendor/revanced/apply.sh --check
   ```

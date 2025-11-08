# ReVanced Prebuilts
This repo contains helper files to integrate ReVanced prebuilts.

## Usage

1. Clone this repo under vendor/revanced
   ```sh
   git clone https://github.com/PixelLineage/vendor_revanced vendor/revanced
   ```
2. Inherit in your vendor or device tree  
   ```mk
   $(call inherit-product, vendor/revanced/products/revanced.mk)
   ```
3. Use the [j-hc revanced project](https://github.com/j-hc/revanced-magisk-module) to create the root module and extract APKs.

4. Place stock and patched APKs  
   - Put the stock app (com.google.android.youtube.apk): `common/product/app/YouTube/YouTube.apk`
   - Put the patched ReVanced app (base.apk): `common/product/etc/rv/YouTube_patched.apk`

5. Run the included script to extract libs:
   ```sh
   ./extract-libs.sh
   ```
   This will extract required libs into their respective lib folders.

6. Pick these two commits  
   - [fwb: disable auto-updates for revanced apps](https://github.com/PixelLineage/frameworks_base/commit/bc71449a25b6b0d16d2b4e611cdc9939bd89bb54)
   - [settings: allow disabling rom-side revanced apps](https://github.com/PixelLineage/packages_apps_Settings/commit/38def62c73e175bf65708137c3e9e281c476ba84)

7. Build the ROM and enjoy  

## Note
The prebuilts present in this repo are just placeholders.

## Acknowledgements
- [j-hc/revanced-magisk-module](https://github.com/j-hc/revanced-magisk-module)
- ReVanced team

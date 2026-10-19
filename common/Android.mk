# ReVanced Prebuilt Apps
LOCAL_PATH := $(call my-dir)

# Stock YouTube
# A presigned app, so release signing (sign_target_files_apks) keeps Google's
# signature instead of stopping on an APK it has no key for.
include $(CLEAR_VARS)
LOCAL_MODULE        := YouTube
LOCAL_SRC_FILES     := product/app/YouTube/YouTube.apk
LOCAL_MODULE_CLASS  := APPS
LOCAL_MODULE_SUFFIX := .apk
LOCAL_CERTIFICATE   := PRESIGNED
# Installed byte for byte: aligning or uncompressing it would break the v2/v3
# signature.
LOCAL_REPLACE_PREBUILT_APK_INSTALLED := $(LOCAL_PATH)/product/app/YouTube/YouTube.apk
LOCAL_DEX_PREOPT    := false
LOCAL_PRODUCT_MODULE := true
include $(BUILD_PREBUILT)

# Patched YouTube
# Only a bind-mount source (init.rv.rc), not a package: installed without the
# .apk extension so release signing leaves it alone.
include $(CLEAR_VARS)
LOCAL_MODULE            := YouTube_patched
LOCAL_SRC_FILES         := product/etc/rv/YouTube_patched.apk
LOCAL_MODULE_CLASS      := ETC
LOCAL_MODULE_TAGS       := optional
LOCAL_PRODUCT_MODULE    := true
LOCAL_MODULE_PATH       := $(TARGET_OUT_PRODUCT)/etc/rv
LOCAL_INSTALLED_MODULE_STEM := YouTube_patched.rv
include $(BUILD_PREBUILT)

# Copy YT native libs
include $(CLEAR_VARS)
LOCAL_MODULE := YouTube_libdir
LOCAL_MODULE_CLASS := ETC
LOCAL_PRODUCT_MODULE := true
LOCAL_MODULE_PATH := $(TARGET_OUT_PRODUCT)/app/YouTube/lib
LOCAL_PREBUILT_MODULE_FILE := $(LOCAL_PATH)/product/app/YouTube/lib/placeholder.txt
LOCAL_POST_INSTALL_CMD := \
    mkdir -p $(LOCAL_MODULE_PATH); \
    cp -rf $(LOCAL_PATH)/product/app/YouTube/lib/* $(LOCAL_MODULE_PATH)/
include $(BUILD_PREBUILT)


# Stock YTMusic (presigned app, see YouTube)
include $(CLEAR_VARS)
LOCAL_MODULE        := YTMusic
LOCAL_SRC_FILES     := product/app/YTMusic/YTMusic.apk
LOCAL_MODULE_CLASS  := APPS
LOCAL_MODULE_SUFFIX := .apk
LOCAL_CERTIFICATE   := PRESIGNED
# Installed byte for byte: aligning or uncompressing it would break the v2/v3
# signature.
LOCAL_REPLACE_PREBUILT_APK_INSTALLED := $(LOCAL_PATH)/product/app/YTMusic/YTMusic.apk
LOCAL_DEX_PREOPT    := false
LOCAL_PRODUCT_MODULE := true
include $(BUILD_PREBUILT)

# Patched YTMusic (bind-mount source, see YouTube_patched)
include $(CLEAR_VARS)
LOCAL_MODULE            := YTMusic_patched
LOCAL_SRC_FILES         := product/etc/rv/YTMusic_patched.apk
LOCAL_MODULE_CLASS      := ETC
LOCAL_MODULE_TAGS       := optional
LOCAL_PRODUCT_MODULE    := true
LOCAL_MODULE_PATH       := $(TARGET_OUT_PRODUCT)/etc/rv
LOCAL_INSTALLED_MODULE_STEM := YTMusic_patched.rv
include $(BUILD_PREBUILT)

# Copy YTMusic native libs
include $(CLEAR_VARS)
LOCAL_MODULE := YTMusic_libdir
LOCAL_MODULE_CLASS := ETC
LOCAL_PRODUCT_MODULE := true
LOCAL_MODULE_PATH := $(TARGET_OUT_PRODUCT)/app/YTMusic/lib
LOCAL_PREBUILT_MODULE_FILE := $(LOCAL_PATH)/product/app/YTMusic/lib/placeholder.txt
LOCAL_POST_INSTALL_CMD := \
    mkdir -p $(LOCAL_MODULE_PATH); \
    cp -rf $(LOCAL_PATH)/product/app/YTMusic/lib/* $(LOCAL_MODULE_PATH)/
include $(BUILD_PREBUILT)

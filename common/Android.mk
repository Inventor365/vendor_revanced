# ReVanced Prebuilt Apps
LOCAL_PATH := $(call my-dir)

# Stock YouTube
include $(CLEAR_VARS)
LOCAL_MODULE        := YouTube
LOCAL_SRC_FILES     := product/app/YouTube/YouTube.apk
LOCAL_MODULE_CLASS  := ETC
LOCAL_MODULE_PATH   := $(TARGET_OUT_PRODUCT)/app/YouTube
LOCAL_INSTALLED_MODULE_STEM := YouTube.apk
LOCAL_PRODUCT_MODULE := true
include $(BUILD_PREBUILT)

# Patched YouTube
include $(CLEAR_VARS)
LOCAL_MODULE            := YouTube_patched
LOCAL_SRC_FILES         := product/etc/rv/YouTube_patched.apk
LOCAL_MODULE_CLASS      := ETC
LOCAL_MODULE_TAGS       := optional
LOCAL_PRODUCT_MODULE    := true
LOCAL_MODULE_PATH       := $(TARGET_OUT_PRODUCT)/etc/rv
LOCAL_INSTALLED_MODULE_STEM := YouTube_patched.apk
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


# Stock YTMusic
include $(CLEAR_VARS)
LOCAL_MODULE        := YTMusic
LOCAL_SRC_FILES     := product/app/YTMusic/YTMusic.apk
LOCAL_MODULE_CLASS  := ETC
LOCAL_MODULE_PATH   := $(TARGET_OUT_PRODUCT)/app/YTMusic
LOCAL_INSTALLED_MODULE_STEM := YTMusic.apk
LOCAL_PRODUCT_MODULE := true
include $(BUILD_PREBUILT)

# Patched YTMusic
include $(CLEAR_VARS)
LOCAL_MODULE            := YTMusic_patched
LOCAL_SRC_FILES         := product/etc/rv/YTMusic_patched.apk
LOCAL_MODULE_CLASS      := ETC
LOCAL_MODULE_TAGS       := optional
LOCAL_PRODUCT_MODULE    := true
LOCAL_MODULE_PATH       := $(TARGET_OUT_PRODUCT)/etc/rv
LOCAL_INSTALLED_MODULE_STEM := YTMusic_patched.apk
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

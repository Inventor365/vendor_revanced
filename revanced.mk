#
# ReVanced ROM Product Configuration
#
# Inherit this makefile from your device's device.mk:
#   $(call inherit-product, vendor/revanced/revanced.mk)
#
# SPDX-License-Identifier: Apache-2.0
#

ifndef REVANCED_PRODUCT_INCLUDED
REVANCED_PRODUCT_INCLUDED := true

ifneq ($(TARGET_DISABLE_REVANCED),true)

-include vendor/revanced/common/prepared.mk

# Verify required vendor/revanced prebuilt APKs, extracted native libs, init & sepolicy exist
ifeq ($(wildcard vendor/revanced/common/product/app/YouTube/YouTube.apk),)
$(error vendor/revanced: Missing common/product/app/YouTube/YouTube.apk. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/etc/rv/YouTube_patched.apk),)
$(error vendor/revanced: Missing common/product/etc/rv/YouTube_patched.apk. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/app/YouTube/lib/placeholder.txt),)
$(error vendor/revanced: Missing extracted YouTube native libraries. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/app/YTMusic/YTMusic.apk),)
$(error vendor/revanced: Missing common/product/app/YTMusic/YTMusic.apk. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/etc/rv/YTMusic_patched.apk),)
$(error vendor/revanced: Missing common/product/etc/rv/YTMusic_patched.apk. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/app/YTMusic/lib/placeholder.txt),)
$(error vendor/revanced: Missing extracted YTMusic native libraries. Run: bash vendor/revanced/apply.sh)
endif
ifeq ($(wildcard vendor/revanced/common/product/etc/init/init.rv.rc),)
$(error vendor/revanced: Missing common/product/etc/init/init.rv.rc)
endif
ifeq ($(wildcard vendor/revanced/sepolicy/private/revanced_init.te),)
$(error vendor/revanced: Missing sepolicy/private/revanced_init.te)
endif

# Verify required frameworks/base and packages/apps/Settings source files exist
ifeq ($(wildcard frameworks/base/core/java/android/app/ApplicationPackageManager.java),)
$(error vendor/revanced: Missing frameworks/base/core/java/android/app/ApplicationPackageManager.java)
endif
ifeq ($(wildcard frameworks/base/services/core/java/com/android/server/pm/PackageInstallerService.java),)
$(error vendor/revanced: Missing frameworks/base/services/core/java/com/android/server/pm/PackageInstallerService.java)
endif
ifeq ($(wildcard frameworks/base/services/core/java/com/android/server/pm/PackageInstallerSession.java),)
$(error vendor/revanced: Missing frameworks/base/services/core/java/com/android/server/pm/PackageInstallerSession.java)
endif
ifeq ($(wildcard packages/apps/Settings/src/com/android/settings/applications/AppDashboardFragment.java),)
$(error vendor/revanced: Missing packages/apps/Settings/src/com/android/settings/applications/AppDashboardFragment.java)
endif
ifeq ($(wildcard packages/apps/Settings/res/xml/apps.xml),)
$(error vendor/revanced: Missing packages/apps/Settings/res/xml/apps.xml)
endif

# Verify framework and Settings integration has been prepared
ifeq ($(REVANCED_SOURCE_PREPARED)$(wildcard packages/apps/Settings/res/values/revanced_strings.xml),)
$(error vendor/revanced: Framework and Settings patches are not prepared. Run: bash vendor/revanced/apply.sh)
endif

$(call inherit-product, vendor/revanced/common/common-vendor.mk)

# Sepolicy
PRODUCT_PRIVATE_SEPOLICY_DIRS += \
    vendor/revanced/sepolicy/private

# Init
PRODUCT_COPY_FILES += \
    vendor/revanced/common/product/etc/init/init.rv.rc:$(TARGET_COPY_OUT_PRODUCT)/etc/init/init.rv.rc

# Enable by default
PRODUCT_PRODUCT_PROPERTIES += \
    persist.sys.revan.mod=true

endif # TARGET_DISABLE_REVANCED != true
endif # REVANCED_PRODUCT_INCLUDED

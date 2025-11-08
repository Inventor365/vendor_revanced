$(call inherit-product, vendor/revanced/common/common-vendor.mk)

# Sepolicy
PRODUCT_PRIVATE_SEPOLICY_DIRS += vendor/revanced/sepolicy/private

# Init
PRODUCT_COPY_FILES += \
    vendor/revanced/common/product/etc/init/init.rv.rc:$(TARGET_COPY_OUT_PRODUCT)/etc/init/init.rv.rc

# Enable by default
PRODUCT_PRODUCT_PROPERTIES += \
    persist.sys.revan.mod=true

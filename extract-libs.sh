rm -rf common/product/app/YouTube/lib
unzip -o common/product/app/YouTube/YouTube.apk "lib/arm64-v8a/*" -d common/product/app/YouTube
mv common/product/app/YouTube/lib/arm64-v8a common/product/app/YouTube/lib/arm64
touch common/product/app/YouTube/lib/placeholder.txt

rm -rf common/product/app/YTMusic/lib
unzip -o common/product/app/YTMusic/YTMusic.apk "lib/arm64-v8a/*" -d common/product/app/YTMusic
mv common/product/app/YTMusic/lib/arm64-v8a common/product/app/YTMusic/lib/arm64
touch common/product/app/YTMusic/lib/placeholder.txt
rm -rf common/product/app/YouTube/lib
unzip -o common/product/app/YouTube/YouTube.apk "lib/arm64-v8a/*" -d common/product/app/YouTube
mv common/product/app/YouTube/lib/arm64-v8a common/product/app/YouTube/lib/arm64
touch common/product/app/YouTube/lib/placeholder.txt

rm -rf common/product/app/Music/lib
unzip -o common/product/app/Music/Music.apk "lib/arm64-v8a/*" -d common/product/app/Music
mv common/product/app/Music/lib/arm64-v8a common/product/app/Music/lib/arm64
touch common/product/app/Music/lib/placeholder.txt
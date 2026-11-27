#!/bin/sh
# Copies the native libraries of an APK you already have (your own build of
# this app) into android/app/libs/arm64-v8a, so that `./gradlew assembleDebug`
# builds THIS source (Kazakh strings included) with those libraries. This
# skips the ReXGlue SDK and the codegen from your game dump, which
# android/build_apk.sh needs.
#
# The libraries are game-derived. They stay in android/app/libs/, which git
# ignores, and must never be committed or published.
#
# Usage: sh android/use_apk_libs.sh path/to/RaymanOrigins-0.5.0.apk
set -e
APK=${1:?usage: sh android/use_apk_libs.sh path/to/app.apk}
A=$(cd "$(dirname "$0")" && pwd)
LIBS=$A/app/libs/arm64-v8a
mkdir -p "$LIBS"
python3 - "$APK" "$LIBS" <<'PY'
import os, sys, zipfile
apk, out = sys.argv[1], sys.argv[2]
need = ["librayman.so", "librexruntime.so", "librexgpu-xenos.so", "librexgpu-null.so", "libc++_shared.so"]
z = zipfile.ZipFile(apk)
names = set(z.namelist())
missing = [n for n in need if "lib/arm64-v8a/" + n not in names]
if missing:
    sys.exit("this APK has no game libraries (missing: %s)" % ", ".join(missing))
for n in need:
    with z.open("lib/arm64-v8a/" + n) as src, open(os.path.join(out, n), "wb") as dst:
        dst.write(src.read())
    print("copied", n)
PY
echo "Next: cd android && ./gradlew assembleDebug"
echo "APK: $A/app/build/outputs/apk/debug/app-debug.apk"

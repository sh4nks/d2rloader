#!/usr/bin/env bash
# Builds dist/D2RLoader.AppImage from the current checkout.
#
# The AppImage bundles a wheel built from this checkout, so the tagged commit
# is what ships, not whatever the default branch looks like at build time.
#
# PySide6 ships Qt's xcb platform plugin without the xcb helper libraries it
# links against (libxcb-cursor, libxcb-icccm, ...). Those are copied from the
# build host into the bundled Qt lib directory, which is why the host's glibc
# sets the minimum glibc of the resulting AppImage.
#
# python-appimage assembles the AppDir from an --appimage-extract of its base
# Python AppImage. Since type2-runtime 8f39b89 that extraction creates every
# directory with mode 0700, which appimagetool then packs as is. Such an
# AppImage still runs via FUSE, which does not enforce permissions, but not
# where the squashfs is kernel-mounted and run as another user, e.g. inside
# firejail ("AppRun: Permission denied"). So the AppDir is made world-readable
# before packaging, and the smoke test checks the modes stored in the AppImage
# with unsquashfs (squashfs-tools), since --appimage-extract would not show them.
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
ARCH="$(uname -m)"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT/resources/appimage"
BUILD_DIR="$ROOT/build/appimage"
APP_DIR="$BUILD_DIR/d2rloader"
EXTRA_DIR="$BUILD_DIR/extra"
QT_LIB_DIR="$EXTRA_DIR/opt/python$PYTHON_VERSION/lib/python$PYTHON_VERSION/site-packages/PySide6/Qt/lib"
APPDIR_OUT="$BUILD_DIR/D2RLoader-$ARCH"
OUTPUT="$ROOT/dist/D2RLoader.AppImage"

QT_XCB_LIBS=(
  libxkbcommon.so.0
  libxkbcommon-x11.so.0
  libxcb-cursor.so.0
  libxcb-icccm.so.4
  libxcb-image.so.0
  libxcb-keysyms.so.1
  libxcb-randr.so.0
  libxcb-render.so.0
  libxcb-render-util.so.0
  libxcb-shape.so.0
  libxcb-shm.so.0
  libxcb-sync.so.1
  libxcb-util.so.1
  libxcb-xfixes.so.0
  libxcb-xkb.so.1
)

log() { printf '==> %s\n' "$*"; }

find_library() {
  ldconfig -p | awk -v lib="$1" '$1 == lib && !found { print $NF; found = 1 }'
}

run_python() {
  uv run --locked --only-group linux --project "$ROOT" python "$@"
}

command -v unsquashfs > /dev/null \
  || { echo "error: unsquashfs (squashfs-tools) is required for the smoke test" >&2; exit 1; }

log "Preparing $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$APP_DIR" "$QT_LIB_DIR" "$(dirname "$OUTPUT")"

log "Building wheel"
uv build --wheel --out-dir "$BUILD_DIR" "$ROOT"
WHEEL="$(ls "$BUILD_DIR"/d2rloader-*.whl)"
VERSION="$(basename "$WHEEL" | cut -d- -f2)"

log "Staging AppDir metadata for d2rloader $VERSION"
cp -L "$SOURCE_DIR"/d2rloader.desktop "$SOURCE_DIR"/d2rloader.appdata.xml \
  "$SOURCE_DIR"/d2rloader.png "$SOURCE_DIR"/entrypoint.sh "$APP_DIR/"
echo "$WHEEL" > "$APP_DIR/requirements.txt"

log "Staging Qt xcb platform plugin dependencies"
for lib in "${QT_XCB_LIBS[@]}"; do
  path="$(find_library "$lib")"
  if [ -z "$path" ]; then
    echo "error: $lib is not installed on this host" >&2
    exit 1
  fi
  cp -L "$path" "$QT_LIB_DIR/"
done

log "Building AppDir with python-appimage"
(
  cd "$BUILD_DIR"
  run_python -m python_appimage build app \
    --python-version "$PYTHON_VERSION" \
    --no-packaging \
    "$APP_DIR" \
    --extra-data "$EXTRA_DIR/opt"
)

log "Making $APPDIR_OUT world-readable"
chmod -R a+rX "$APPDIR_OUT"

log "Packaging $APPDIR_OUT with appimagetool"
run_python -c 'import sys; from python_appimage.appimage import build_appimage; build_appimage(sys.argv[1], destination=sys.argv[2])' \
  "$APPDIR_OUT" "$OUTPUT"

log "Smoke testing $OUTPUT"
(
  cd "$BUILD_DIR"
  rm -rf squashfs-root
  unsquashfs -no-progress -d squashfs-root -offset "$("$OUTPUT" --appimage-offset)" "$OUTPUT" > /dev/null
  not_world_readable="$(find squashfs-root ! -perm -o=r -o -type d ! -perm -o=x)"
  if [ -n "$not_world_readable" ]; then
    echo "error: not world-readable inside the AppImage:" >&2
    echo "$not_world_readable" >&2
    exit 1
  fi
  bundled_version="$(
    squashfs-root/usr/bin/python"$PYTHON_VERSION" -I -c \
      'import importlib.metadata, d2rloader.app; print(importlib.metadata.version("d2rloader"))'
  )"
  if [ "$bundled_version" != "$VERSION" ]; then
    echo "error: AppImage bundles d2rloader $bundled_version, expected $VERSION" >&2
    exit 1
  fi
  for lib in "${QT_XCB_LIBS[@]}"; do
    test -f "squashfs-root/${QT_LIB_DIR#"$EXTRA_DIR/"}/$lib" \
      || { echo "error: $lib missing from AppImage" >&2; exit 1; }
  done
  rm -rf squashfs-root
)

log "Built $OUTPUT ($(du -h "$OUTPUT" | cut -f1), d2rloader $VERSION)"

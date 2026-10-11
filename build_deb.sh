#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_TMP="/tmp/genpen-build-$$"
OUTPUT_DIR="${REPO_DIR}/releases"
DEB_NAME="gen-pen_2.0.0-1_all.deb"

echo "=== Building Gen Pen Debian Package ==="
mkdir -p "${BUILD_TMP}" "${OUTPUT_DIR}"

# 1. Control & Metadata
mkdir -p "${BUILD_TMP}/DEBIAN"
cp "${REPO_DIR}/debian/control" "${BUILD_TMP}/DEBIAN/control"
cp "${REPO_DIR}/debian/postinst" "${BUILD_TMP}/DEBIAN/postinst"
cp "${REPO_DIR}/debian/postrm" "${BUILD_TMP}/DEBIAN/postrm"
chmod 755 "${BUILD_TMP}/DEBIAN/postinst" "${BUILD_TMP}/DEBIAN/postrm"

# 2. Executable launcher
mkdir -p "${BUILD_TMP}/usr/bin"
cp "${REPO_DIR}/desktop/bin/genpen" "${BUILD_TMP}/usr/bin/genpen"
ln -sf /usr/bin/genpen "${BUILD_TMP}/usr/bin/gen-pen"
chmod 755 "${BUILD_TMP}/usr/bin/genpen"

# 3. Application Python core
mkdir -p "${BUILD_TMP}/usr/lib/genpen/assets/fonts"
cp "${REPO_DIR}/desktop/app/genpen_app.py" "${BUILD_TMP}/usr/lib/genpen/genpen_app.py"
cp "${REPO_DIR}/desktop/app/genpen_mantle_bridge.py" "${BUILD_TMP}/usr/lib/genpen/genpen_mantle_bridge.py"
cp "${REPO_DIR}/desktop/bin/genpen-cleaner.sh" "${BUILD_TMP}/usr/lib/genpen/genpen-cleaner.sh"
chmod 755 "${BUILD_TMP}/usr/lib/genpen/genpen-cleaner.sh"
cp "${REPO_DIR}/desktop/assets/fonts/MaterialIcons-Regular.ttf" "${BUILD_TMP}/usr/lib/genpen/assets/fonts/MaterialIcons-Regular.ttf"

# 4. Systemd Timer & Service for ephemeral storage cleanup
mkdir -p "${BUILD_TMP}/usr/lib/systemd/user"
cp "${REPO_DIR}/desktop/systemd/"* "${BUILD_TMP}/usr/lib/systemd/user/"

# 5. Desktop Application Integration (.desktop & icons)
mkdir -p "${BUILD_TMP}/usr/share/applications"
cp "${REPO_DIR}/desktop/genpen.desktop" "${BUILD_TMP}/usr/share/applications/genpen.desktop"
cp "${REPO_DIR}/desktop/genpen.desktop" "${BUILD_TMP}/usr/share/applications/tr.org.genpen.desktop"

mkdir -p "${BUILD_TMP}/usr/share/icons"
cp -r "${REPO_DIR}/desktop/assets/icons/hicolor" "${BUILD_TMP}/usr/share/icons/"

mkdir -p "${BUILD_TMP}/usr/share/pixmaps"
cp "${REPO_DIR}/desktop/assets/icons/hicolor/scalable/apps/genpen.svg" "${BUILD_TMP}/usr/share/pixmaps/genpen.svg"
cp "${REPO_DIR}/desktop/assets/icons/hicolor/scalable/apps/genpen.svg" "${BUILD_TMP}/usr/share/pixmaps/tr.org.genpen.svg"
cp "${REPO_DIR}/desktop/assets/icons/hicolor/128x128/apps/genpen.png" "${BUILD_TMP}/usr/share/pixmaps/genpen.png"
cp "${REPO_DIR}/desktop/assets/icons/hicolor/128x128/apps/genpen.png" "${BUILD_TMP}/usr/share/pixmaps/tr.org.genpen.png"

# 6. Build .deb
echo "Packaging with dpkg-deb..."
dpkg-deb --build "${BUILD_TMP}" "${OUTPUT_DIR}/${DEB_NAME}"
rm -rf "${BUILD_TMP}"

echo "Debian package successfully built at: ${OUTPUT_DIR}/${DEB_NAME}"
ls -lh "${OUTPUT_DIR}/${DEB_NAME}"

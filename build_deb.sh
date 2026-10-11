#!/usr/bin/env bash
# ==============================================================================
# Gen Pen — Debian package builder
#
# Assembles the installation tree from the repository sources and produces an
# installable .deb with dpkg-deb. Package name, version and architecture are
# read from debian/control, so a version bump only requires editing that file.
#
# Usage:
#   ./build_deb.sh                    # -> releases/<package>_<version>_<arch>.deb
#   OUTPUT_DIR=dist ./build_deb.sh    # -> dist/<package>_<version>_<arch>.deb
# ==============================================================================
set -euo pipefail
umask 022

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP="${REPO_DIR}/desktop"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_DIR}/releases}"

# --- Package metadata ---------------------------------------------------------
control_field() {
    sed -n "s/^$1:[[:space:]]*//p" "${REPO_DIR}/debian/control" | head -n 1
}

PACKAGE="$(control_field Package)"
VERSION="$(control_field Version)"
ARCH="$(control_field Architecture)"
DEB_NAME="${PACKAGE}_${VERSION}_${ARCH}.deb"

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "error: dpkg-deb not found — please install the 'dpkg' package." >&2
    exit 1
fi

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/genpen-build.XXXXXX")"
trap 'rm -rf "${BUILD_DIR}"' EXIT
PKG_ROOT="${BUILD_DIR}/root"
install -d -m 755 "${PKG_ROOT}"

echo "==> Building ${DEB_NAME}"

# --- 1. Control file & maintainer scripts -------------------------------------
install -d -m 755 "${PKG_ROOT}/DEBIAN"
install -m 644 "${REPO_DIR}/debian/control"  "${PKG_ROOT}/DEBIAN/control"
install -m 755 "${REPO_DIR}/debian/postinst" "${PKG_ROOT}/DEBIAN/postinst"
install -m 755 "${REPO_DIR}/debian/postrm"   "${PKG_ROOT}/DEBIAN/postrm"

# --- 2. Launcher (+ "gen-pen" alias) ------------------------------------------
install -D -m 755 "${DESKTOP}/bin/genpen" "${PKG_ROOT}/usr/bin/genpen"
ln -s genpen "${PKG_ROOT}/usr/bin/gen-pen"

# --- 3. Application code & bundled Material Icons font ------------------------
LIB_DIR="${PKG_ROOT}/usr/lib/genpen"
install -D -m 755 "${DESKTOP}/app/genpen_app.py"           "${LIB_DIR}/genpen_app.py"
install -D -m 644 "${DESKTOP}/app/genpen_mantle_bridge.py" "${LIB_DIR}/genpen_mantle_bridge.py"
install -D -m 755 "${DESKTOP}/bin/genpen-cleaner.sh"       "${LIB_DIR}/genpen-cleaner.sh"
install -D -m 644 "${DESKTOP}/assets/fonts/MaterialIcons-Regular.ttf" \
                  "${LIB_DIR}/assets/fonts/MaterialIcons-Regular.ttf"

# --- 4. systemd user units (daily cleanup of received images) -----------------
install -d -m 755 "${PKG_ROOT}/usr/lib/systemd/user"
install -m 644 "${DESKTOP}/systemd/genpen-cleaner.service" \
               "${DESKTOP}/systemd/genpen-cleaner.timer" \
               "${PKG_ROOT}/usr/lib/systemd/user/"

# --- 5. Desktop entry -----------------------------------------------------------
APPS_DIR="${PKG_ROOT}/usr/share/applications"
install -D -m 644 "${DESKTOP}/genpen.desktop" "${APPS_DIR}/genpen.desktop"
install -m 644    "${DESKTOP}/genpen.desktop" "${APPS_DIR}/tr.org.genpen.desktop"

# --- 6. Icons: hicolor theme (+ reverse-DNS aliases) and pixmaps fallback ------
ICON_SRC="${DESKTOP}/assets/icons/hicolor"
ICON_DST="${PKG_ROOT}/usr/share/icons/hicolor"
for icon in "${ICON_SRC}"/*/apps/genpen.*; do
    rel="${icon#"${ICON_SRC}/"}"          # e.g. 48x48/apps/genpen.png
    install -D -m 644 "${icon}" "${ICON_DST}/${rel}"
    install -m 644    "${icon}" "${ICON_DST}/$(dirname "${rel}")/tr.org.genpen.${icon##*.}"
done

PIXMAPS_DIR="${PKG_ROOT}/usr/share/pixmaps"
install -d -m 755 "${PIXMAPS_DIR}"
for name in genpen tr.org.genpen; do
    install -m 644 "${ICON_SRC}/scalable/apps/genpen.svg" "${PIXMAPS_DIR}/${name}.svg"
    install -m 644 "${ICON_SRC}/128x128/apps/genpen.png"  "${PIXMAPS_DIR}/${name}.png"
done

# --- 7. Build the package -------------------------------------------------------
# -Zxz keeps the archive installable on every Debian-based release (Ubuntu's
# dpkg defaults to zstd); --root-owner-group makes every file owned by root.
mkdir -p "${OUTPUT_DIR}"
dpkg-deb -Zxz --root-owner-group --build "${PKG_ROOT}" "${OUTPUT_DIR}/${DEB_NAME}"

echo "==> Package ready: ${OUTPUT_DIR}/${DEB_NAME}"
ls -lh "${OUTPUT_DIR}/${DEB_NAME}"

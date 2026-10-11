# Pardus 23 ETAP Smartboard Integration Guide

## 1. System Requirements
- **OS**: Pardus 23 (ETAP / XFCE / GNOME) or Debian 12 (Bookworm) / Ubuntu 22.04+
- **Display Resolution**: 1280x800, 1920x1080 (Full HD), or 3840x2160 (4K UHD)
- **Input Devices**: Infrared touch frame, capacitive multi-touch screen, active/passive stylus pen, or standard mouse
- **Dependencies**: `python3`, `python3-pyqt6`, `python3-pil`, `python3-requests`, `python3-qrcode`

## 2. Desktop Menu Integration (FreeDesktop Standard)
The package automatically installs:
- Desktop specification file: `/usr/share/applications/genpen.desktop`
  - Accessible from the system Application Menu under:
    - **Eğitim (Education)**
    - **Grafik (Graphics)**
    - **Donatılar (Utility)**
- Application Icon Set:
  - Scalable vector: `/usr/share/icons/hicolor/scalable/apps/genpen.svg`
  - High-resolution rasters:
    - `/usr/share/icons/hicolor/512x512/apps/genpen.png`
    - `/usr/share/icons/hicolor/256x256/apps/genpen.png`
    - `/usr/share/icons/hicolor/128x128/apps/genpen.png`
    - `/usr/share/icons/hicolor/64x64/apps/genpen.png`
    - `/usr/share/icons/hicolor/48x48/apps/genpen.png`
    - `/usr/share/icons/hicolor/32x32/apps/genpen.png`
  - Pixmaps fallback: `/usr/share/pixmaps/genpen.png`
- Triggers:
  - During `.deb` installation, `update-desktop-database` and `gtk-update-icon-cache` run automatically.

## 3. Ephemeral Storage Cleaner Service
Smartboards in shared classrooms accumulate temporary media files over time. Gen Pen installs a systemd user timer:
- `/usr/lib/systemd/user/genpen-cleaner.service`
- `/usr/lib/systemd/user/genpen-cleaner.timer`
- Cleans questions older than 24 hours from `/tmp/genpen_incoming/` to prevent disk bloat.

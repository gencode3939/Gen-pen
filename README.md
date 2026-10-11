# Gen Pen 🖊️

**Next-Generation Smartboard Drawing & Mobile Question Transfer System for Pardus 23 GNU/Linux**

[![GitHub Release](https://img.shields.io/github/v/release/gencode3939/Gen-pen?color=blue&logo=github)](https://github.com/gencode3939/Gen-pen/releases)
[![Platform](https://img.shields.io/badge/Platform-Pardus%2023%20%7C%20Debian%2012%20%7C%20Linux-blue?logo=linux)](https://www.pardus.org.tr/)
[![Framework](https://img.shields.io/badge/UI-PyQt6%20%7C%20Qt6-green?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![Design](https://img.shields.io/badge/Design-Google%20Material%203-4285F4?logo=google)](https://m3.material.io/)
[![Package](https://img.shields.io/badge/Download-.deb%20(v2.0.0)-D70A53?logo=debian)](https://github.com/gencode3939/Gen-pen/releases/download/v2.0.0/gen-pen_2.0.0-1_all.deb)
[![Offline](https://img.shields.io/badge/Offline-100%25%20Ready%20(Local%20Fonts)-success)](#features)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 📖 Overview

**Gen Pen** is a modern, high-performance interactive whiteboard and screen annotation application specifically crafted for **Pardus 23 (ETAP)** smartboards in classrooms and lecture halls. 

It provides an unobstructed, **true edge-to-edge frameless canvas**, an **animated floating dock** with long-press touch invocation, bundled local **Google Material Design 3 icons**, and an **instant mobile question transfer bridge** powered by a secure 6-digit PIN.

Teachers and students can snap questions from textbooks, crop and enhance contrast directly on their phones, and transmit them straight onto the smartboard canvas in real time with zero pairing hurdles.

---

## 📸 Screenshots Gallery

| 1. Fullscreen Canvas & Unified Dock | 2. Floating Pill FAB (Collapsed Mode) |
| :---: | :---: |
| ![Unified Dock](docs/screenshots/smartboard_fullscreen.png) | ![Collapsed Dock](docs/screenshots/smartboard_dock_collapsed.png) |
| *Edge-to-edge canvas with all tools consolidated into the bottom dock.* | *Zero distractions. Hold down anywhere on screen to animate the dock back up.* |

| 3. Smartboard Templates Menu | 4. Real-time Question Annotation |
| :---: | :---: |
| ![Templates Menu](docs/screenshots/smartboard_templates.png) | ![Question Solved](docs/screenshots/smartboard_question_solved.png) |
| *Switch between Whiteboard, Blackboard, Grid, Lined, and Music Staff.* | *Mobile question received via PIN and solved on math grid paper.* |

| 5. Safe Touchscreen Exit Dialog |
| :---: |
| ![Exit Dialog](docs/screenshots/smartboard_exit_dialog.png) |
| *High-quality confirmation modal preventing accidental touchscreen dismissals.* |

---

## ✨ Key Features

### 1. 🖥️ True Frameless Edge-to-Edge Canvas
- Completely eliminates top header bars, window decorations, and desktop borders.
- The drawing canvas spans 100% of the display dimensions (1280x800, 1080p, 4K UHD).
- Inspired by Pardus-Pen and ETA-Pen smartboard specifications.

### 2. 🎛️ Unified Animated Floating Dock (`GenDock`)
- **All Controls in One Place**: Drawing tools, 6 quick colors, unlimited palette, continuous width slider, board templates, mobile PIN indicator, undo/redo, clear canvas, fullscreen toggle, collapse, and exit.
- **Fluid Physics Animations**: Slides down into a compact floating pill (`✏️ Gen Pen ^`) with cubic easing (`QEasingCurve.Type.OutCubic`).
- **Touch Hold (Long-Press) Activation**: Press and hold anywhere on the screen for **380 ms** to trigger an animated ripple ring and bring the dock smoothly back into view.

### 3. 🎨 100% Offline Google Material Icons (Zero CDN Dependency)
- The official Google Material Icons TrueType font (`MaterialIcons-Regular.ttf`) is bundled directly inside the `.deb` package at `/usr/lib/genpen/assets/fonts/`.
- The companion mobile app embeds the WOFF2 font inline via base64.
- High-speed, crisp rendering with zero network latency, guaranteed to work in offline, air-gapped schools.

### 4. 📱 Frictionless 6-Digit PIN Mobile Companion (No QR Codes)
- Connects smartphones to the smartboard via a simple, memorable **6-Digit PIN** (e.g. `581 604`).
- Automatically remembers the last entered PIN in browser `localStorage`.
- Built-in camera capture, gallery picker, touch crop box, and contrast boost filter for crisp textbook legibility.
- Non-blocking cloud/local synchronization powered by MantleDB v2 REST API.

### 5. 📐 Multi-Disciplinary Board Templates
- ⚪ **Pure Whiteboard**: Pristine white canvas for standard diagramming and notes.
- ⚫ **Classic Blackboard**: Matte dark slate background optimized for chalk-like contrast.
- 🔲 **Math Grid Notebook**: Clean squared grid for geometry, algebra, and physics graphs.
- 📝 **Lined Notebook**: Ruled lines for handwriting, essays, and language classes.
- 🎼 **Music Staff**: 5-line musical staves for notation and music theory.

### 6. 🖊️ Natural Drawing & Annotation Tools
- **Pen**: Precision vector drawing with smoothed cubic Bezier interpolation.
- **Calligraphy**: Nib-angle chisel stroke engine with dynamic stroke variation.
- **Highlighter**: Semi-transparent marker with multiply composite blending.
- **Laser Pointer**: Glowing transient indicator that automatically dissolves after 2.5 seconds.
- **Segment Eraser**: Fast hit-tested erasing of strokes and elements.
- **Geometric Shapes**: Draw lines, directional vectors/arrows, rectangles, ellipses, and triangles.

### 7. 🚪 Desktop Menu Integration & Safe Touchscreen Exit
- Standard FreeDesktop specification files (`genpen.desktop`) installed into `/usr/share/applications/`.
- Full set of Hicolor icons from 16x16 to 512x512 plus scalable SVG.
- Dedicated red-accented Exit button on the dock with a touch-friendly confirmation dialog to prevent accidental closures.

---

## 🚀 Quick Start & Installation

### Option A: Install via Pre-built Debian Package (Pardus 23 / Debian / Ubuntu)

Download the ready-to-install package from the `releases/` folder or build it locally:

```bash
# Install the Debian package
sudo dpkg -i releases/gen-pen_2.0.0-1_all.deb

# Resolve any missing runtime dependencies automatically
sudo apt-get install -f
```

Launch Gen Pen:
- From the system menu: **Uygulamalar -> Eğitim -> Gen Pen**
- Or from terminal:
```bash
genpen
```

### Option B: Run from Source

```bash
# 1. Clone the repository
git clone https://github.com/gencode3939/Gen-pen.git
cd Gen-pen

# 2. Install required system dependencies (Debian/Ubuntu/Pardus)
sudo apt-get update
sudo apt-get install -y python3 python3-pyqt6 python3-pil python3-requests python3-qrcode

# 3. Launch the desktop application
python3 desktop/app/genpen_app.py
```

---

## 📱 Using the Mobile Companion

1. Open `mobile/index.html` on your phone (or host it on a local web server / PWA).
2. Enter the **6-Digit PIN** shown in the smartboard's dock (e.g. `581 604`).
3. Tap **Fotoğraf Çek** (Take Photo) or **Galeriden Seç** (Choose from Gallery).
4. Crop the question box and tap **Kontrastı Artır** (Boost Contrast) if lighting is dim.
5. Tap **Tahtaya Gönder** (Send to Board). The question will instantly appear on the smartboard!

---

## ⌨️ Shortcuts & Gestures

| Action | Mouse / Touch / Keyboard |
| :--- | :--- |
| **Open Dock** | **Long-Press** (hold for 380 ms anywhere on screen) or click `✏️ Gen Pen ^` |
| **Hide Dock** | Click `🔽` on the dock or press <kbd>Esc</kbd> |
| **Toggle Fullscreen** | Click `⛶` on the dock or press <kbd>F11</kbd> |
| **Exit Application** | Click `⏻` (Power button) or press <kbd>Ctrl</kbd> + <kbd>Q</kbd> |
| **Undo Stroke** | Click `↺` or press <kbd>Ctrl</kbd> + <kbd>Z</kbd> |
| **Redo Stroke** | Click `↻` or press <kbd>Ctrl</kbd> + <kbd>Y</kbd> |
| **Move Image** | Select Hand tool (`pan_tool`), touch and drag the question box |

---

## 📂 Repository Structure

```
genpen/
├── .github/
│   └── workflows/
│       └── build-deb.yml          # Automated CI/CD Debian package build workflow
├── desktop/                       # Desktop application source
│   ├── app/
│   │   ├── genpen_app.py          # Main PyQt6 smartboard application
│   │   └── genpen_mantle_bridge.py# MantleDB cloud sync worker
│   ├── assets/
│   │   ├── fonts/
│   │   │   └── MaterialIcons-Regular.ttf # Local offline Google Material font
│   │   └── icons/                 # Hicolor vector and raster icons (16px to 512px)
│   ├── bin/
│   │   ├── genpen                 # Standard binary launcher script
│   │   └── genpen-cleaner.sh      # Cache cleanup script
│   ├── systemd/                   # Systemd ephemeral storage cleaner unit & timer
│   └── genpen.desktop             # FreeDesktop standard desktop entry
├── mobile/                        # Offline-first mobile web companion (PWA)
│   ├── index.html                 # Standalone web app with embedded Material Icons
│   ├── manifest.json              # PWA manifest
│   ├── sw.js                      # Service Worker for offline caching
│   └── assets/fonts/              # WOFF2 Material Icons
├── debian/                        # Debian packaging specifications
│   ├── control                    # Package metadata & dependencies
│   ├── postinst                   # Desktop database & icon cache update trigger
│   └── postrm                     # Clean uninstallation script
├── docs/                          # Technical documentation & screenshots
│   ├── ARCHITECTURE.md            # Zero-mock architecture & REST API details
│   ├── PARDUS_INTEGRATION.md      # Pardus 23 ETAP integration guide
│   └── screenshots/               # Verified UI screenshots
├── releases/
│   └── gen-pen_2.0.0-1_all.deb    # Pre-built installable Debian package
├── build_deb.sh                   # One-click script to build .deb from source
├── LICENSE                        # Apache License 2.0
├── .gitignore                     # Git ignore rules
└── README.md                      # English documentation
```

---

## 🛠️ Building the Debian Package

To rebuild the installable `.deb` package at any time:

```bash
chmod +x build_deb.sh
./build_deb.sh
```

The resulting package will be output to `releases/gen-pen_2.0.0-1_all.deb`.

---

## 📄 License & Attribution

This project is open source and licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for full details.

- Designed for the **Pardus GNU/Linux** ecosystem and Fatih Smartboard Project (ETAP).
- Icons provided by [Google Material Design](https://fonts.google.com/icons).
- Real-time synchronization powered by [MantleDB](https://mantledb.sh).

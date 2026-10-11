# Gen Pen Technical Architecture & Pipeline

## 1. Overview
Gen Pen is structured into two core components that communicate seamlessly without local network restrictions or pairing hurdles:
1. **Desktop Smartboard Client (`desktop/`)**: Built in Python 3 with PyQt6, designed to run natively on Linux smartboards (Pardus 23 ETAP, Debian 12, Ubuntu 22.04+).
2. **Mobile Web Companion (`mobile/`)**: An offline-first Progressive Web App (PWA) running locally on student or teacher smartphones (iOS Safari, Android Chrome).

```
 ┌──────────────────────┐                     ┌──────────────────────────────┐
 │ Mobile Companion App │                     │   Gen Pen Desktop Client     │
 │  (Any Smartphone)    │                     │   (Pardus 23 Smartboard)     │
 └──────────┬───────────┘                     └──────────────▲───────────────┘
            │                                                │
   1. Enter 6-digit PIN                             5. Polls every 1.2s
   2. Snap/Select question                             via MantleWorker
   3. Crop & enhance contrast                                │
   4. POST to MantleDB REST API                              │
            │                                                │
            └───────────────► ┌────────────────────┐ ────────┘
                              │  MantleDB Cloud    │
                              │  Namespace:        │
                              │  genpen-pin-{PIN}  │
                              └────────────────────┘
```

## 2. Zero-Mock Communication Pipeline
- **Namespace Generation**: When Gen Pen launches on the smartboard, `MantleWorker` registers a 6-digit PIN (e.g. `581604`). It claims a dedicated namespace `genpen-pin-581604` using the MantleDB v2 API (`GET https://mantledb.sh/v2/claim/genpen-pin-{PIN}`).
- **Payload Transmission**: The mobile device uploads the captured image as base64 JSON payload to `POST https://mantledb.sh/v2/genpen-pin-{PIN}/incoming`.
- **Background Worker**: `MantleWorker` runs on a non-blocking `QThread` polling every 1.2s. Once a payload arrives, it emits `mediaReceived(QPixmap, sender, path)`.
- **Canvas Placement**: The smartboard automatically places the question image directly in the center of the active canvas with smooth drop shadow and interactive drag handles.

## 3. UI/UX Architecture
- **Frameless Fullscreen**: The root `GenMainWindow` adopts `Qt.WindowType.FramelessWindowHint` and directly maps to `primaryScreen().geometry()`, ensuring true edge-to-edge drawing canvas with no borders.
- **Unified Bottom Dock (`GenDock`)**:
  - Contains all tools (Pan, Pen, Calligraphy, Highlighter, Laser, Eraser, Shapes dropdown).
  - Quick colors + custom color dialog.
  - Continuous width slider (1px - 48px).
  - Board template switcher menu (Pure Whiteboard, Blackboard, Grid Notebook, Lined Notebook, Sheet Music).
  - Live 6-digit PIN indicator pill.
  - Auto-insert toggle switch.
  - Undo, Redo, Clear Canvas, Fullscreen toggle, Dock Collapse.
  - Dedicated red-accented Exit button with modal confirmation dialog.
- **Long-Press Activation**:
  - `GenCanvas` tracks touch and mouse presses. If held for 380ms, a subtle blue ripple is drawn at the contact point and `dock.slide_up_animated()` smoothly reveals the dock.
- **Local Google Material Icons**:
  - The TrueType font `MaterialIcons-Regular.ttf` is bundled locally inside `/usr/lib/genpen/assets/fonts/`.
  - Zero external web CDN dependencies, guaranteeing 100% offline functionality in air-gapped classrooms.

# Pardus 23 ETAP Integration Guide

How Gen Pen integrates with Pardus 23 ETAP smartboards (and other Debian-based
systems): requirements, installed files, menu integration, background services
and network needs.

- [1. System requirements](#1-system-requirements)
- [2. Installation](#2-installation)
- [3. Installed files](#3-installed-files)
- [4. Application menu](#4-application-menu)
- [5. Package maintainer scripts](#5-package-maintainer-scripts)
- [6. Daily cache cleanup](#6-daily-cache-cleanup)
- [7. Network & firewall](#7-network--firewall)
- [8. Uninstallation](#8-uninstallation)

---

## 1. System requirements

| | |
| :--- | :--- |
| **Operating system** | Pardus 23 (ETAP / XFCE / GNOME), Debian 12 (Bookworm), Ubuntu 22.04 or newer |
| **Display** | Any resolution — e.g. 1280 × 800, 1920 × 1080, 3840 × 2160. The canvas always fills the primary screen. |
| **Input** | Infrared touch frame, capacitive multi-touch screen, stylus or mouse |
| **Runtime dependencies** | `python3`, `python3-pyqt6`, `python3-qrcode`, `python3-pil`, `python3-requests` |
| **Network** | Optional. Needed only for the mobile question transfer (see [§7](#7-network--firewall)). |

## 2. Installation

```bash
sudo apt install ./gen-pen_2.0.0-1_all.deb
```

`apt` resolves the runtime dependencies automatically. When installing with
`dpkg -i` instead, run `sudo apt-get install -f` afterwards to pull in missing
dependencies.

## 3. Installed files

| Path | Purpose |
| :--- | :--- |
| `/usr/bin/genpen` | Launcher (`exec python3 /usr/lib/genpen/genpen_app.py "$@"`) |
| `/usr/bin/gen-pen` | Symlink to `genpen` |
| `/usr/lib/genpen/genpen_app.py` | Desktop application |
| `/usr/lib/genpen/genpen_mantle_bridge.py` | Standalone MantleDB bridge (console test tool) |
| `/usr/lib/genpen/genpen-cleaner.sh` | Daily cache cleanup script |
| `/usr/lib/genpen/assets/fonts/MaterialIcons-Regular.ttf` | Bundled Material Icons font (offline UI icons) |
| `/usr/lib/systemd/user/genpen-cleaner.service` | systemd user service that runs the cleanup script |
| `/usr/lib/systemd/user/genpen-cleaner.timer` | systemd user timer — daily at 00:00 |
| `/usr/share/applications/genpen.desktop` | Application menu entry |
| `/usr/share/applications/tr.org.genpen.desktop` | Same entry under the reverse-DNS application id |
| `/usr/share/icons/hicolor/<size>/apps/genpen.png` | Raster icons: 16, 24, 32, 48, 64, 128, 256 and 512 px |
| `/usr/share/icons/hicolor/scalable/apps/genpen.svg` | Scalable vector icon |
| `/usr/share/pixmaps/genpen.{png,svg}` | Legacy fallback icons (128 px PNG and SVG) |

Every icon is also installed as `tr.org.genpen.{png,svg}` next to the
`genpen` variant so that both application ids resolve to the same artwork.

## 4. Application menu

The desktop entry follows the
[freedesktop.org Desktop Entry specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/):

- **Categories:** `Education;Graphics;Utility;` — in category-based menus such
  as XFCE's, Gen Pen is listed under **Eğitim**, **Grafik** and **Donatılar**.
- **Search keywords:** `pen`, `tahta`, `cizim`, `whiteboard`, `fatih`,
  `etkilesimli`, `smartboard`, `drawing`, `annotation`.
- **Localisation:** Turkish by default, English (`[en]`) variants for
  `GenericName`, `Comment` and the actions.
- **Quick actions** (right-click on the launcher): *Beyaz Tahta Modu*
  (`genpen --mode=white`) and *Kara Tahta Modu* (`genpen --mode=black`).

> [!NOTE]
> The application does not interpret `--mode` yet, so both quick actions
> currently open the default white board. Because `genpen.desktop` and
> `tr.org.genpen.desktop` are both visible, some menus list Gen Pen twice.

## 5. Package maintainer scripts

| Script | Actions |
| :--- | :--- |
| [`debian/postinst`](../debian/postinst) | Runs `update-desktop-database` and `gtk-update-icon-cache`, then `systemctl --global enable genpen-cleaner.timer` so the cleanup timer starts for every user at their next login. |
| [`debian/postrm`](../debian/postrm) | Refreshes the desktop database and the icon cache. |

Each step is skipped gracefully when the corresponding tool is not available.

## 6. Daily cache cleanup

Images received from phones are stored per user and per day:

```
~/.cache/genpen/incoming/
├── 2026-10-10/          ← deleted by the next cleanup run
└── 2026-10-11/
    ├── current_session.json
    └── img_101530_mob_1791702930000.jpg
```

On shared classroom boards this folder would grow indefinitely, so the package
ships a systemd **user** timer that runs every night at 00:00
(`Persistent=true`: a missed run is caught up at the next login). It deletes
day folders older than 24 hours.

```bash
systemctl --user status genpen-cleaner.timer        # timer state and next run
systemctl --user start genpen-cleaner.service       # run the cleanup now
journalctl --user -u genpen-cleaner.service         # cleanup log
```

## 7. Network & firewall

Drawing works completely offline. The mobile question transfer additionally
needs **outbound HTTPS (TCP 443) to `mantledb.sh`**:

| Device | Requirement |
| :--- | :--- |
| Smartboard | Must reach `https://mantledb.sh` (polled every 1.2 s while Gen Pen is running) |
| Phone | Must reach `https://mantledb.sh` and the address where `mobile/index.html` is hosted |

If school network filtering blocks unknown domains, ask your network
administrator to allow `mantledb.sh`. Phones on mobile data are not affected by
the school network.

## 8. Uninstallation

```bash
sudo systemctl --global disable genpen-cleaner.timer   # remove the per-user timer link
sudo apt remove gen-pen
rm -rf ~/.cache/genpen                                 # optional, per user
```

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEN PEN - Yeni Nesil Akıllı Tahta & Ekran Çizim Sistemi
Pardus 23 GNU/Linux / Debian 12
Gelişmiş Çizim Motoru, Tam Ekran Yazı Modu, Animasyonlu Yüzen Dock,
Uzun Basma (Long-Press) ile Dock Açma ve Yerel Google Material Icons
"""

import sys
import os
import time
import json
import base64
import math
import shutil
import random
import urllib.request
import urllib.error
from datetime import datetime

from PyQt6.QtCore import (
    Qt, QPoint, QPointF, QRect, QRectF, QSize, QTimer, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPixmap, QImage, QPainterPath,
    QFont, QFontDatabase, QTabletEvent, QMouseEvent, QPaintEvent, QPolygonF,
    QCursor
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDialog, QColorDialog, QMessageBox, QFrame,
    QSlider, QGraphicsDropShadowEffect, QMenu, QCheckBox
)


# =============================================================================
# 0. YEREL GOOGLE MATERIAL ICONS YÜKLEME (OFFLINE & SIFIR GECİKME)
# =============================================================================
MATERIAL_FONT_FAMILY = "Material Icons"

def load_material_font():
    global MATERIAL_FONT_FAMILY
    font_paths = [
        "/usr/lib/genpen/assets/fonts/MaterialIcons-Regular.ttf",
        "/usr/share/fonts/truetype/material-design-icons-iconfont/MaterialIcons-Regular.ttf",
        "/usr/share/fonts/truetype/material-icons/MaterialIcons-Regular.ttf",
        os.path.join(os.path.dirname(__file__), "assets/fonts/MaterialIcons-Regular.ttf"),
        # Kaynak koddan çalıştırma: desktop/app/ -> desktop/assets/fonts/
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "assets", "fonts", "MaterialIcons-Regular.ttf"),
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            fid = QFontDatabase.addApplicationFont(fp)
            if fid >= 0:
                fams = QFontDatabase.applicationFontFamilies(fid)
                if fams:
                    MATERIAL_FONT_FAMILY = fams[0]
                    print(f"[GenPen] Material Icons Fontu Yüklendi: '{MATERIAL_FONT_FAMILY}'")
                    return
    print("[GenPen] Uyarı: Material Icons fontu bulunamadı, varsayılan font kullanılacak.")

# Material Icons Unicode Kodları
ICONS = {
    "pan": "",          # pan_tool (taşıma)
    "pen": "",          # edit (normal kalem)
    "calligraphy": "",  # brush (dolma/kaligrafi)
    "highlighter": "",  # highlight (vurgu)
    "laser": "",        # flash_on / bolt (lazer)
    "eraser": "",       # backspace (silgi)
    "shapes": "",       # category (şekiller)
    "palette": "",      # palette (renk seçici)
    "board": "",        # grid_on (tahta şablonları & arka plan)
    "auto_on": "",      # auto_awesome (otomatik soru ekleme)
    "undo": "",         # undo (geri al)
    "redo": "",         # redo (yinele)
    "clear": "",        # delete_sweep (tuvali temizle)
    "mobile": "",       # smartphone (mobil PIN)
    "collapse": "",     # keyboard_arrow_down (dock gizle)
    "expand": "",       # keyboard_arrow_up (dock aç)
    "fullscreen": "",   # fullscreen (tam ekran)
    "exit": "",         # power_settings_new (uygulamadan çıkış)
}


# =============================================================================
# 1. MATERIAL ICON BUTONU
# =============================================================================
class MaterialIconButton(QPushButton):
    def __init__(self, icon_char, tooltip="", checkable=False, checked=False, width=38, height=38, parent=None):
        super().__init__(parent)
        self.setToolTip(tooltip)
        self.setCheckable(checkable)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(width, height)
        self.setFont(QFont(MATERIAL_FONT_FAMILY, 19))
        self.setText(icon_char)

        self.setStyleSheet("""
            QPushButton {
                background-color: #F1F3F4;
                color: #1F1F1F;
                border: 1px solid #DADCE0;
                border-radius: 19px;
            }
            QPushButton:hover {
                background-color: #E8F0FE;
                color: #1A73E8;
                border-color: #1A73E8;
            }
            QPushButton:checked {
                background-color: #D3E3FD;
                color: #041E49;
                border: 2px solid #1A73E8;
            }
        """)


# =============================================================================
# 2. MANTLEDB ARKA PLAN DİNLEYİCİSİ (6 HANELİ SINIF PIN SİSTEMİ)
# =============================================================================
class MantleWorker(QThread):
    roomReady = pyqtSignal(str) # pinCode
    mediaReceived = pyqtSignal(QPixmap, str, str) # pixmap, sender, filePath

    MANTLE_BASE_URL = "https://mantledb.sh/v2"

    def __init__(self, pin_code=None):
        super().__init__()
        self.pin_code = pin_code or str(random.randint(100000, 999999))
        self.namespace = f"genpen-pin-{self.pin_code}"
        self.is_running = True
        self.last_received_id = None

        cache_base = os.path.expanduser("~/.cache/genpen")
        self.today_dir = os.path.join(cache_base, "incoming", datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(self.today_dir, exist_ok=True)

    def run(self):
        print(f"[MantleDB] Aktif Sınıf PIN: {self.pin_code} (Namespace: {self.namespace})")

        try:
            with open(os.path.join(self.today_dir, "current_session.json"), "w") as sf:
                json.dump({"pin": self.pin_code, "namespace": self.namespace}, sf)
        except Exception:
            pass

        self.roomReady.emit(self.pin_code)

        headers = {"User-Agent": "GenPen-Pardus23/2.0"}
        while self.is_running:
            try:
                poll_url = f"{self.MANTLE_BASE_URL}/{self.namespace}/incoming"
                poll_req = urllib.request.Request(poll_url, headers=headers)
                with urllib.request.urlopen(poll_req, timeout=4) as poll_resp:
                    poll_data = json.loads(poll_resp.read().decode("utf-8"))
                    if isinstance(poll_data, dict) and "data" in poll_data:
                        msg_id = str(poll_data.get("id") or poll_data.get("timestamp"))
                        if msg_id != self.last_received_id:
                            self.last_received_id = msg_id
                            self._process_incoming(poll_data)
            except urllib.error.HTTPError:
                pass
            except Exception:
                pass
            time.sleep(1.2)

    def _process_incoming(self, data):
        try:
            raw_b64 = data.get("data", "")
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            pix = QPixmap()
            if pix.loadFromData(img_bytes):
                ts = datetime.now().strftime("%H%M%S")
                fname = f"img_{ts}_{data.get('id', 'upload')}.jpg"
                fpath = os.path.join(self.today_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(img_bytes)
                sender = data.get("sender", "Öğrenci / Telefon")
                self.mediaReceived.emit(pix, sender, fpath)
        except Exception as e:
            print(f"[MantleDB] Görsel işleme hatası: {e}")

    def stop(self):
        self.is_running = False


# =============================================================================
# 3. DONANIM ÇİZİM MOTORU (GENCANVAS) - UZUN BASMA & TAM EKRAN ÇİZİM
# =============================================================================
class GenCanvas(QWidget):
    longPressTriggered = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True if hasattr(Qt.WidgetAttribute, 'WA_AcceptTouchEvents') else False)
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents, True)
        self.setMouseTracking(True)

        self.canvas_mode = "white"
        self.overlay_mode = "none"
        self.active_tool = "pen" # pan, pen, calligraphy, highlighter, laser, eraser, shape
        self.active_shape = "line"
        
        self.brush_color = QColor("#1A73E8")
        self.base_width = 5.0
        self.pressure_enabled = True

        self.strokes = []
        self.undone_strokes = []
        self.current_stroke = []
        self.images = []

        # Lazer İzleri
        self.laser_points = []
        self.laser_timer = QTimer(self)
        self.laser_timer.timeout.connect(self._update_laser)
        self.laser_timer.start(45)

        # Şekiller
        self.shape_start = None
        self.shape_current = None

        # Görsel Taşıma
        self.dragged_image = None
        self.drag_offset = QPointF()

        self.last_point = None
        self.last_time = 0

        # Uzun Basma (Long-Press) Dedektörü
        self.press_pos = QPointF()
        self.is_long_pressed = False
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._on_long_press_timeout)

        # Dokunmatik Halka Animasyonu (Ripple)
        self.ripple_pos = None
        self.ripple_radius = 0.0
        self.ripple_alpha = 240
        self.ripple_timer = QTimer(self)
        self.ripple_timer.timeout.connect(self._step_ripple)

        self.setStyleSheet("background-color: #FFFFFF;")

    def set_canvas_mode(self, mode):
        self.canvas_mode = mode
        if mode == "white":
            self.setStyleSheet("background-color: #FFFFFF;")
        elif mode == "black":
            self.setStyleSheet("background-color: #1E1E1E;")
        elif mode == "transparent":
            self.setStyleSheet("background-color: transparent;")
        self.update()

    def set_overlay_mode(self, mode):
        self.overlay_mode = mode
        self.update()

    def set_active_tool(self, tool):
        self.active_tool = tool
        self.shape_start = None

    def set_active_shape(self, shape):
        self.active_shape = shape
        self.active_tool = "shape"

    def set_brush_color(self, color):
        self.brush_color = QColor(color)
        self.update()

    def set_base_width(self, width):
        self.base_width = max(1.0, float(width))

    def clear_canvas(self):
        self.strokes.clear()
        self.undone_strokes.clear()
        self.images.clear()
        self.update()

    def undo(self):
        if self.strokes:
            self.undone_strokes.append(self.strokes.pop())
            self.update()

    def redo(self):
        if self.undone_strokes:
            self.strokes.append(self.undone_strokes.pop())
            self.update()

    def insert_image(self, pixmap, pos=None):
        if pixmap.isNull():
            return
        w = self.width()
        h = self.height()
        max_w = w * 0.75
        max_h = h * 0.75
        scaled = pixmap
        if pixmap.width() > max_w or pixmap.height() > max_h:
            scaled = pixmap.scaled(int(max_w), int(max_h), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        if pos is None:
            pos = QPointF((w - scaled.width()) / 2.0, (h - scaled.height()) / 2.0)

        rect = QRectF(pos.x(), pos.y(), scaled.width(), scaled.height())
        self.images.append({"pixmap": scaled, "rect": rect, "selected": False})
        self.update()

    def _calc_dynamic_width(self, pressure, velocity):
        if not self.pressure_enabled or pressure <= 0.0:
            return self.base_width

        if self.active_tool == "calligraphy":
            p_factor = 0.2 + 0.8 * math.pow(pressure, 1.5)
            v_factor = 1.0 - 0.2 * min(1.0, velocity / 1200.0)
            return self.base_width * 1.5 * p_factor * v_factor
        elif self.active_tool == "highlighter":
            return max(20.0, self.base_width * 3.5)
        else:
            p_factor = 0.4 + 0.6 * math.pow(pressure, 1.2)
            return self.base_width * p_factor

    def _add_point(self, pos, pressure):
        now = time.time() * 1000.0
        vel = 0.0
        if self.last_time > 0 and now > self.last_time and self.last_point:
            dist = math.hypot(pos.x() - self.last_point.x(), pos.y() - self.last_point.y())
            vel = (dist / (now - self.last_time)) * 1000.0

        w = self._calc_dynamic_width(pressure, vel)

        if self.active_tool == "laser":
            self.laser_points.append({"pos": QPointF(pos), "time": now, "alpha": 255})
        else:
            self.current_stroke.append({
                "pos": QPointF(pos),
                "pressure": pressure,
                "width": w,
                "time": now
            })

        self.last_point = QPointF(pos)
        self.last_time = now

    def _finish_stroke(self):
        if len(self.current_stroke) > 0 and self.active_tool != "laser":
            self.strokes.append({
                "type": "freehand",
                "points": list(self.current_stroke),
                "color": QColor(self.brush_color),
                "base_width": self.base_width,
                "tool": self.active_tool
            })
            self.undone_strokes.clear()
            self.current_stroke.clear()
        self.last_point = None
        self.last_time = 0
        self.update()

    def _finish_shape(self):
        if self.shape_start and self.shape_current:
            self.strokes.append({
                "type": "shape",
                "shape": self.active_shape,
                "start": QPointF(self.shape_start),
                "end": QPointF(self.shape_current),
                "color": QColor(self.brush_color),
                "width": self.base_width
            })
            self.undone_strokes.clear()
            self.shape_start = None
            self.shape_current = None
            self.update()

    def _update_laser(self):
        if not self.laser_points:
            return
        now = time.time() * 1000.0
        surviving = []
        for lp in self.laser_points:
            age = now - lp["time"]
            if age < 1200:
                lp["alpha"] = max(0, int(255 * (1.0 - age / 1200.0)))
                surviving.append(lp)
        self.laser_points = surviving
        self.update()

    # Uzun Basma Tetikleyicisi (Long-Press Handler)
    def _on_long_press_timeout(self):
        self.is_long_pressed = True
        self.current_stroke.clear()
        self.ripple_pos = QPointF(self.press_pos)
        self.ripple_radius = 8.0
        self.ripple_alpha = 240
        self.ripple_timer.start(16)
        self.longPressTriggered.emit(self.press_pos)
        self.update()

    def _step_ripple(self):
        self.ripple_radius += 3.5
        self.ripple_alpha -= 16
        if self.ripple_alpha <= 0:
            self.ripple_timer.stop()
            self.ripple_pos = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self.press_pos = pos
            self.is_long_pressed = False

            # 380 ms boyunca basılı tutulduğunda dock animasyonla açılır
            self.long_press_timer.start(380)

            # Taşıma aracı aktifse görselleri taşı
            if self.active_tool == "pan":
                for img in reversed(self.images):
                    if img["rect"].contains(pos):
                        self.dragged_image = img
                        self.drag_offset = pos - img["rect"].topLeft()
                        self.long_press_timer.stop()
                        return

            if self.active_tool == "shape":
                self.shape_start = pos
                self.shape_current = pos
                self.update()
                return

            self.current_stroke = []
            self._add_point(pos, 0.5)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.position()

            # 8 pikselden fazla hareket varsa uzun basma iptal (normal çizimdir)
            if (pos - self.press_pos).manhattanLength() > 8:
                self.long_press_timer.stop()

            if self.is_long_pressed:
                return

            if self.dragged_image:
                new_top_left = pos - self.drag_offset
                self.dragged_image["rect"].moveTopLeft(new_top_left)
                self.update()
                return

            if self.active_tool == "shape" and self.shape_start:
                self.shape_current = pos
                self.update()
                return

            self._add_point(pos, 0.5)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.stop()

            if self.is_long_pressed:
                self.is_long_pressed = False
                self.current_stroke.clear()
                self.update()
                return

            if self.dragged_image:
                self.dragged_image = None
                return

            if self.active_tool == "shape":
                self._finish_shape()
                return

            self._finish_stroke()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self.canvas_mode == "white":
            painter.fillRect(self.rect(), QColor("#FFFFFF"))
        elif self.canvas_mode == "black":
            painter.fillRect(self.rect(), QColor("#1E1E1E"))

        self._draw_grid_overlay(painter)

        # Görseller
        for item in self.images:
            pix = item["pixmap"]
            r = item["rect"]
            painter.drawPixmap(int(r.x()), int(r.y()), pix)
            if self.active_tool == "pan":
                painter.setPen(QPen(QColor(26, 115, 232, 220), 2.5, Qt.PenStyle.DashLine))
                painter.drawRoundedRect(r, 6, 6)

        # Çizimler
        for s in self.strokes:
            if s.get("type") == "shape":
                self._draw_shape_item(painter, s)
            else:
                self._draw_stroke_item(painter, s)

        if self.current_stroke:
            temp_stroke = {
                "points": self.current_stroke,
                "color": self.brush_color,
                "base_width": self.base_width,
                "tool": self.active_tool
            }
            self._draw_stroke_item(painter, temp_stroke)

        if self.shape_start and self.shape_current:
            temp_shape = {
                "shape": self.active_shape,
                "start": self.shape_start,
                "end": self.shape_current,
                "color": self.brush_color,
                "width": self.base_width
            }
            self._draw_shape_item(painter, temp_shape)

        self._draw_laser_trail(painter)

        # Uzun Basma Dokunmatik Halka Animasyonu (Ripple)
        if self.ripple_pos and self.ripple_alpha > 0:
            c = QColor(26, 115, 232, self.ripple_alpha)
            painter.setPen(QPen(c, 3))
            painter.setBrush(QBrush(QColor(26, 115, 232, int(self.ripple_alpha * 0.3))))
            painter.drawEllipse(self.ripple_pos, self.ripple_radius, self.ripple_radius)

    def _draw_grid_overlay(self, painter):
        if self.overlay_mode == "none" or self.canvas_mode == "transparent":
            return
        grid_col = QColor(220, 224, 230) if self.canvas_mode == "white" else QColor(55, 60, 70)
        painter.setPen(QPen(grid_col, 1))

        if self.overlay_mode == "grid":
            step = 32
            for x in range(0, self.width(), step):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), step):
                painter.drawLine(0, y, self.width(), y)
        elif self.overlay_mode == "lines":
            step = 36
            for y in range(step, self.height(), step):
                painter.drawLine(0, y, self.width(), y)
        elif self.overlay_mode == "music":
            line_gap = 12
            group_gap = 60
            for start_y in range(70, self.height() - 70, (line_gap * 4 + group_gap)):
                for l in range(5):
                    y = start_y + l * line_gap
                    painter.drawLine(40, y, self.width() - 40, y)

    def _draw_stroke_item(self, painter, stroke):
        pts = stroke["points"]
        if len(pts) < 2:
            return

        tool = stroke["tool"]
        draw_color = QColor(stroke["color"])

        if tool == "highlighter":
            draw_color.setAlpha(90)
        elif tool == "eraser":
            if self.canvas_mode == "white":
                draw_color = QColor("#FFFFFF")
            elif self.canvas_mode == "black":
                draw_color = QColor("#1E1E1E")
            else:
                draw_color = QColor(0, 0, 0, 0)

        for i in range(len(pts) - 1):
            p1 = pts[i]["pos"]
            p2 = pts[i + 1]["pos"]
            w = pts[i]["width"]
            pen = QPen(draw_color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(p1, p2)

    def _draw_shape_item(self, painter, shape):
        p1 = shape["start"]
        p2 = shape["end"]
        color = shape["color"]
        w = shape["width"]
        s_type = shape["shape"]

        pen = QPen(color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if s_type == "line":
            painter.drawLine(p1, p2)
        elif s_type == "arrow":
            painter.drawLine(p1, p2)
            angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            arrow_size = 14 + w
            arrow_p1 = QPointF(p2.x() - arrow_size * math.cos(angle - math.pi / 6),
                               p2.y() - arrow_size * math.sin(angle - math.pi / 6))
            arrow_p2 = QPointF(p2.x() - arrow_size * math.cos(angle + math.pi / 6),
                               p2.y() - arrow_size * math.sin(angle + math.pi / 6))
            painter.setBrush(QBrush(color))
            painter.drawPolygon(QPolygonF([p2, arrow_p1, arrow_p2]))
        elif s_type == "rect":
            r = QRectF(p1, p2).normalized()
            painter.drawRoundedRect(r, 6, 6)
        elif s_type == "circle":
            r = QRectF(p1, p2).normalized()
            painter.drawEllipse(r)
        elif s_type == "triangle":
            top = QPointF((p1.x() + p2.x()) / 2, min(p1.y(), p2.y()))
            bl = QPointF(min(p1.x(), p2.x()), max(p1.y(), p2.y()))
            br = QPointF(max(p1.x(), p2.x()), max(p1.y(), p2.y()))
            painter.drawPolygon(QPolygonF([top, bl, br]))

    def _draw_laser_trail(self, painter):
        for lp in self.laser_points:
            c = QColor(255, 40, 40, lp["alpha"])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(lp["pos"], 6, 6)


# =============================================================================
# 4. ANİMASYONLU MATERIAL 3 YÜZEN DOCK (GENDOCK - TÜM KONTROLLER TEK NOKTADA)
# =============================================================================
class GenDock(QWidget):
    openPinRequested = pyqtSignal()
    clearRequested = pyqtSignal()
    fullscreenRequested = pyqtSignal()
    exitRequested = pyqtSignal()

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.is_collapsed = False
        self.pin_code = ""

        self._setup_ui()
        self._apply_styles()

        # Kayma Animasyonu
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(260)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _create_divider(self):
        div = QFrame(self.expanded_box)
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Plain)
        div.setFixedWidth(1)
        div.setFixedHeight(24)
        div.setStyleSheet("background-color: #DADCE0; margin: 0 2px;")
        return div

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Genişletilmiş Ana Dock
        self.expanded_box = QFrame(self)
        self.expanded_box.setObjectName("expandedBox")
        box_layout = QHBoxLayout(self.expanded_box)
        box_layout.setContentsMargins(12, 6, 12, 6)
        box_layout.setSpacing(5)

        # Sürükleme Tutamacı
        lbl_drag = QLabel("⋮⋮", self.expanded_box)
        lbl_drag.setStyleSheet("color: #747775; font-size: 16px; font-weight: bold; margin-right: 2px;")
        box_layout.addWidget(lbl_drag)

        # Taşı & Seç
        self.btn_pan = MaterialIconButton(ICONS["pan"], "Soruları ve Görselleri Taşı", checkable=True)
        self.btn_pan.clicked.connect(lambda: self._select_tool("pan", self.btn_pan))
        box_layout.addWidget(self.btn_pan)

        # Kalemler Grubu
        self.btn_pen = MaterialIconButton(ICONS["pen"], "Normal Kalem", checkable=True, checked=True)
        self.btn_pen.clicked.connect(lambda: self._select_tool("pen", self.btn_pen))
        box_layout.addWidget(self.btn_pen)

        self.btn_calligraphy = MaterialIconButton(ICONS["calligraphy"], "Dolma & Kaligrafi Kalemi", checkable=True)
        self.btn_calligraphy.clicked.connect(lambda: self._select_tool("calligraphy", self.btn_calligraphy))
        box_layout.addWidget(self.btn_calligraphy)

        self.btn_highlighter = MaterialIconButton(ICONS["highlighter"], "Fosforlu Vurgu Kalemi", checkable=True)
        self.btn_highlighter.clicked.connect(lambda: self._select_tool("highlighter", self.btn_highlighter))
        box_layout.addWidget(self.btn_highlighter)

        self.btn_laser = MaterialIconButton(ICONS["laser"], "Geçici Lazer İşaretçi", checkable=True)
        self.btn_laser.clicked.connect(lambda: self._select_tool("laser", self.btn_laser))
        box_layout.addWidget(self.btn_laser)

        self.btn_eraser = MaterialIconButton(ICONS["eraser"], "Segment Silgisi", checkable=True)
        self.btn_eraser.clicked.connect(lambda: self._select_tool("eraser", self.btn_eraser))
        box_layout.addWidget(self.btn_eraser)

        # Geometrik Şekiller Menüsü
        self.btn_shapes = MaterialIconButton(ICONS["shapes"], "Geometrik Şekiller (Çizgi, Ok, Dikdörtgen, Çember)")
        shape_menu = QMenu(self.btn_shapes)
        shape_menu.setStyleSheet(
            "QMenu { background-color: #FFFFFF; border: 1px solid #DADCE0; border-radius: 12px; padding: 6px; font-size: 13px; font-weight: 500; } "
            "QMenu::item { padding: 8px 16px; border-radius: 8px; color: #3C4043; } "
            "QMenu::item:selected { background-color: #E8F0FE; color: #1A73E8; }"
        )
        shape_menu.addAction("Düz Çizgi", lambda: self.canvas.set_active_shape("line"))
        shape_menu.addAction("Ok / Vektör", lambda: self.canvas.set_active_shape("arrow"))
        shape_menu.addAction("Dikdörtgen", lambda: self.canvas.set_active_shape("rect"))
        shape_menu.addAction("Çember / Daire", lambda: self.canvas.set_active_shape("circle"))
        shape_menu.addAction("Üçgen", lambda: self.canvas.set_active_shape("triangle"))
        self.btn_shapes.setMenu(shape_menu)
        box_layout.addWidget(self.btn_shapes)

        box_layout.addWidget(self._create_divider())

        # 6 Hızlı Renk
        quick_colors = ["#1A73E8", "#D93025", "#1E8E3E", "#F9AB00", "#1F1F1F", "#9334E8"]
        for hex_code in quick_colors:
            btn_c = QPushButton(self.expanded_box)
            btn_c.setFixedSize(26, 26)
            btn_c.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_c.setStyleSheet(f"background-color: {hex_code}; border-radius: 13px; border: 2px solid #FFF;")
            btn_c.clicked.connect(lambda ch, c=hex_code: self.canvas.set_brush_color(c))
            box_layout.addWidget(btn_c)

        # Sınırsız Renk Seçici (Palet)
        btn_palette = MaterialIconButton(ICONS["palette"], "Sınırsız Renk Seçici (HEX/RGB/HSV)")
        btn_palette.setStyleSheet(
            "QPushButton { background-color: #E8F0FE; color: #1A73E8; border: 1.5px solid #1A73E8; border-radius: 19px; } "
            "QPushButton:hover { background-color: #1A73E8; color: #FFFFFF; }"
        )
        btn_palette.clicked.connect(self._open_color_dialog)
        box_layout.addWidget(btn_palette)

        # Kalınlık Slider & Piksel Göstergesi
        self.lbl_w = QLabel("5px", self.expanded_box)
        self.lbl_w.setStyleSheet("font-size:12px; font-weight:bold; color:#1A73E8; min-width: 28px; text-align: center;")
        box_layout.addWidget(self.lbl_w)
        
        self.slider_width = QSlider(Qt.Orientation.Horizontal, self.expanded_box)
        self.slider_width.setRange(1, 48)
        self.slider_width.setValue(5)
        self.slider_width.setFixedWidth(65)
        self.slider_width.valueChanged.connect(self._on_width_changed)
        box_layout.addWidget(self.slider_width)

        box_layout.addWidget(self._create_divider())

        # Tahta Arka Planı (Beyaz, Kara, Kareli, Çizgili, Müzik)
        self.btn_board = MaterialIconButton(ICONS["board"], "Tahta Düzeni & Şablonlar (Beyaz, Kara, Kareli, Çizgili, Müzik)")
        board_menu = QMenu(self.btn_board)
        board_menu.setStyleSheet(
            "QMenu { background-color: #FFFFFF; border: 1px solid #DADCE0; border-radius: 12px; padding: 6px; font-size: 13px; font-weight: 500; } "
            "QMenu::item { padding: 8px 16px; border-radius: 8px; color: #3C4043; } "
            "QMenu::item:selected { background-color: #E8F0FE; color: #1A73E8; }"
        )
        board_menu.addAction("● Saf Beyaz Tahta", lambda: self.canvas.set_canvas_mode("white"))
        board_menu.addAction("○ Kara Tahta", lambda: self.canvas.set_canvas_mode("black"))
        board_menu.addSeparator()
        board_menu.addAction("⊞ Kareli Defter", lambda: self.canvas.set_overlay_mode("grid" if self.canvas.overlay_mode != "grid" else "none"))
        board_menu.addAction("☰ Çizgili Defter", lambda: self.canvas.set_overlay_mode("lines" if self.canvas.overlay_mode != "lines" else "none"))
        board_menu.addAction("🎵 Müzik Portesi", lambda: self.canvas.set_overlay_mode("music" if self.canvas.overlay_mode != "music" else "none"))
        self.btn_board.setMenu(board_menu)
        box_layout.addWidget(self.btn_board)

        # Canlı Mobil PIN Butonu (Pill)
        self.btn_pin = QPushButton("📱 PIN: Bekleniyor...", self.expanded_box)
        self.btn_pin.setFixedHeight(38)
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.setToolTip("Sınıf Bağlantı Kodu (PIN)\nTıklayarak mobil bağlantı detaylarını açın")
        self.btn_pin.setStyleSheet(
            "QPushButton { background-color: #E8F0FE; color: #1A73E8; font-weight: bold; font-size: 12px; border: 1.5px solid #1A73E8; border-radius: 19px; padding: 4px 12px; } "
            "QPushButton:hover { background-color: #1A73E8; color: #FFFFFF; }"
        )
        self.btn_pin.clicked.connect(self.openPinRequested.emit)
        box_layout.addWidget(self.btn_pin)

        # Otomatik Ekleme Toggle Butonu
        self.btn_auto = MaterialIconButton(ICONS["auto_on"], "Mobil Soruları Otomatik Tuvale Ekle (Açık/Kapalı)", checkable=True, checked=True)
        self.btn_auto.setStyleSheet(
            "QPushButton { background-color: #E6F4EA; color: #137333; border: 1.5px solid #1E8E3E; border-radius: 19px; } "
            "QPushButton:hover { background-color: #CEEAD6; } "
            "QPushButton:!checked { background-color: #F1F3F4; color: #747775; border: 1px solid #DADCE0; }"
        )
        box_layout.addWidget(self.btn_auto)

        box_layout.addWidget(self._create_divider())

        # Geri Al / Yinele
        btn_undo = MaterialIconButton(ICONS["undo"], "Geri Al")
        btn_undo.clicked.connect(self.canvas.undo)
        box_layout.addWidget(btn_undo)

        btn_redo = MaterialIconButton(ICONS["redo"], "Yinele")
        btn_redo.clicked.connect(self.canvas.redo)
        box_layout.addWidget(btn_redo)

        # Tuvali Temizle
        btn_clear = MaterialIconButton(ICONS["clear"], "Tuvali Temizle")
        btn_clear.clicked.connect(self.clearRequested.emit)
        box_layout.addWidget(btn_clear)

        # Tam Ekran Butonu
        btn_fs = MaterialIconButton(ICONS["fullscreen"], "Tam Ekran / Pencere")
        btn_fs.clicked.connect(self.fullscreenRequested.emit)
        box_layout.addWidget(btn_fs)

        # Dock Gizle (Katla)
        btn_hide = MaterialIconButton(ICONS["collapse"], "Dock'u Gizle (Ekrana basılı tutarak açabilirsiniz)")
        btn_hide.clicked.connect(self.slide_down_animated)
        box_layout.addWidget(btn_hide)

        # Uygulamadan Çıkış (Kırmızı Vurgulu)
        btn_exit = MaterialIconButton(ICONS["exit"], "Gen Pen'den Çıkış (Kapat)")
        btn_exit.setStyleSheet(
            "QPushButton { background-color: #FCE8E6; color: #D93025; border: 1.5px solid #D93025; border-radius: 19px; } "
            "QPushButton:hover { background-color: #D93025; color: #FFFFFF; }"
        )
        btn_exit.clicked.connect(self.exitRequested.emit)
        box_layout.addWidget(btn_exit)

        main_layout.addWidget(self.expanded_box)

        # 2. Katlanmış Kapsül (Küçük Kayan Hap)
        self.collapsed_box = QFrame(self)
        self.collapsed_box.setObjectName("collapsedBox")
        col_layout = QHBoxLayout(self.collapsed_box)
        col_layout.setContentsMargins(14, 6, 14, 6)

        btn_exp = QPushButton(f"✏️ Gen Pen  {ICONS['expand']}", self.collapsed_box)
        btn_exp.setFont(QFont("sans-serif", 12, QFont.Weight.Bold))
        btn_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp.setStyleSheet("background: transparent; color: white; border: none;")
        btn_exp.clicked.connect(self.slide_up_animated)
        col_layout.addWidget(btn_exp)

        self.collapsed_box.hide()
        main_layout.addWidget(self.collapsed_box)

    def set_pin_code(self, pin):
        self.pin_code = pin
        formatted = f"{pin[:3]} {pin[3:]}" if len(pin) == 6 else pin
        self.btn_pin.setText(f"📱 {formatted}")
        self.btn_pin.setToolTip(f"Sınıf PIN: {formatted}\n(Tıklayarak mobil bağlantı detaylarını görün)")
        self.adjustSize()

    def is_auto_insert(self):
        return self.btn_auto.isChecked()

    def _select_tool(self, tool_name, active_btn):
        self.canvas.set_active_tool(tool_name)
        for b in [self.btn_pan, self.btn_pen, self.btn_calligraphy, self.btn_highlighter, self.btn_laser, self.btn_eraser]:
            b.setChecked(b == active_btn)

    def _on_width_changed(self, val):
        self.lbl_w.setText(f"{val}px")
        self.canvas.set_base_width(val)

    def _open_color_dialog(self):
        color = QColorDialog.getColor(self.canvas.brush_color, self, "Sınırsız Renk Seçici")
        if color.isValid():
            self.canvas.set_brush_color(color)

    def slide_down_animated(self):
        if self.is_collapsed or not self.parent():
            return
        self.is_collapsed = True
        self.expanded_box.hide()
        self.collapsed_box.show()
        self.adjustSize()

        p_w = self.parent().width()
        p_h = self.parent().height()
        target_x = (p_w - self.width()) // 2
        target_y = p_h - self.height() - 14

        self.anim.stop()
        self.anim.setStartValue(QPoint(target_x, p_h + 30))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.start()
        self.raise_()

    def slide_up_animated(self):
        if not self.parent():
            return
        self.is_collapsed = False
        self.collapsed_box.hide()
        self.expanded_box.show()
        self.adjustSize()

        p_w = self.parent().width()
        p_h = self.parent().height()
        target_x = (p_w - self.width()) // 2
        target_y = p_h - self.height() - 20

        self.anim.stop()
        self.anim.setStartValue(QPoint(target_x, p_h + 30))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.start()
        self.raise_()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#expandedBox {
                background-color: rgba(255, 255, 255, 0.98);
                border: 1.5px solid rgba(0, 0, 0, 0.15);
                border-radius: 24px;
            }
            QFrame#collapsedBox {
                background-color: #1A73E8;
                border-radius: 18px;
                border: 2px solid white;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)


# =============================================================================
# 5. ANİMASYONLU BİLDİRİM TOASTI
# =============================================================================
class GenNotificationToast(QFrame):
    openRequested = pyqtSignal(QPixmap, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pixmap = None
        self.current_path = ""
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        self.setObjectName("toastFrame")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        self.lbl_img = QLabel(self)
        self.lbl_img.setFixedSize(54, 54)
        self.lbl_img.setStyleSheet("border-radius: 8px; border: 2px solid #1A73E8;")
        self.lbl_img.setScaledContents(True)
        layout.addWidget(self.lbl_img)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        lbl_title = QLabel("📷 Yeni Soru Geldi!", self)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13.5px; color: #1F1F1F;")
        self.lbl_sender = QLabel("Gönderen: Öğrenci / Telefon", self)
        self.lbl_sender.setStyleSheet("font-size: 11.5px; color: #5F6368;")
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(self.lbl_sender)
        layout.addLayout(text_layout)

        btn_open = QPushButton("Aç ve Ekle", self)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #1A73E8;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12.5px;
                padding: 8px 16px;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover { background-color: #1557B0; }
        """)
        btn_open.clicked.connect(self._on_open_clicked)
        layout.addWidget(btn_open)

        btn_close = QPushButton("✕", self)
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background: transparent; color: #747775; font-size: 15px; border: none;")
        btn_close.clicked.connect(self.hide)
        layout.addWidget(btn_close)

        self.setStyleSheet("""
            QFrame#toastFrame {
                background-color: #FFFFFF;
                border: 2px solid #1A73E8;
                border-radius: 18px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        self._on_open_clicked()
        event.accept()

    def show_notification(self, pixmap, sender, file_path):
        self.current_pixmap = pixmap
        self.current_path = file_path
        self.lbl_img.setPixmap(pixmap.scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        self.lbl_sender.setText(f"Gönderen: {sender}")
        self.adjustSize()

        if self.parent():
            p_w = self.parent().width()
            p_h = self.parent().height()
            self.move(p_w - self.width() - 20, p_h - self.height() - 90)
        self.show()
        self.raise_()

    def _on_open_clicked(self):
        if self.current_pixmap:
            self.openRequested.emit(self.current_pixmap, self.current_path)
        self.hide()


# =============================================================================
# 6. SINIF PIN DİYALOĞU
# =============================================================================
class PinDialog(QDialog):
    def __init__(self, pin_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gen Pen Sınıf Bağlantı Kodu")
        self.setFixedSize(380, 260)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Akıllı Tahta PIN Kodu", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F1F1F;")
        layout.addWidget(title)

        desc = QLabel("Telefondan bağlanmak için aşağıdaki 6 haneli PIN kodunu giriniz:", self)
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #5F6368;")
        layout.addWidget(desc)

        pin_box = QFrame(self)
        pin_box.setStyleSheet("background: #E8F0FE; border-radius: 14px; padding: 10px;")
        pin_layout = QVBoxLayout(pin_box)
        pin_layout.setContentsMargins(0, 0, 0, 0)

        formatted_pin = f"{pin_code[:3]}  {pin_code[3:]}" if len(pin_code) == 6 else pin_code
        lbl_pin_val = QLabel(formatted_pin, pin_box)
        lbl_pin_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_pin_val.setStyleSheet("font-size: 34px; font-weight: 900; color: #1A73E8; letter-spacing: 4px; font-family: monospace;")
        pin_layout.addWidget(lbl_pin_val)
        layout.addWidget(pin_box)

        btn_close = QPushButton("Kapat", self)
        btn_close.setFixedHeight(40)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1A73E8;
                color: #FFFFFF;
                font-weight: bold;
                border-radius: 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1557B0; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# =============================================================================
# 7. ANA PENCERE (TAM EKRAN AKILLI TAHTA)
# =============================================================================
class GenMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gen Pen - Yeni Nesil Akıllı Tahta (Pardus 23)")

        # Tam Ekran Çizim Modu: Çerçevesiz Kenarsız Tam Ekran (eta-pen ve pardus-pen standardı)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1280, 800)

        # 1. Tuval (Tüm Ekranı Kaplar - Üst Bar Yok, Sıfır Dikkat Dağınıklığı)
        self.canvas = GenCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.longPressTriggered.connect(self._on_canvas_long_press)

        # 2. Animasyonlu Yüzen Alt Dock (Tüm Kontroller Tek Noktada)
        self.dock = GenDock(self.canvas, self)
        self.dock.openPinRequested.connect(self.show_pin_dialog)
        self.dock.clearRequested.connect(self._confirm_clear)
        self.dock.fullscreenRequested.connect(self.toggle_fullscreen)
        self.dock.exitRequested.connect(self.confirm_exit)

        # 3. Bildirim Toastı
        self.toast = GenNotificationToast(self)
        self.toast.openRequested.connect(self._on_toast_open)

        # 4. MantleDB Arka Plan Servisi (Gerçek 6 Haneli PIN)
        self.worker = MantleWorker()
        self.worker.roomReady.connect(self._on_room_ready)
        self.worker.mediaReceived.connect(self._on_media_received)
        self.worker.start()

        self.pin_code = ""

    def _on_room_ready(self, pin_code):
        self.pin_code = pin_code
        self.dock.set_pin_code(pin_code)
        print(f"[GenPen UI] Sınıf PIN Kodu Hazır: {pin_code}")

    def _on_media_received(self, pixmap, sender, fpath):
        print(f"[GenPen UI] Görsel Geldi: {sender} -> {fpath}")
        if self.dock.is_auto_insert():
            self.canvas.insert_image(pixmap)
            self.toast.show_notification(pixmap, sender, fpath)
            QTimer.singleShot(4000, self.toast.hide)
        else:
            self.toast.show_notification(pixmap, sender, fpath)

    def _on_toast_open(self, pixmap, fpath):
        if not self.dock.is_auto_insert():
            self.canvas.insert_image(pixmap)
        self.toast.hide()

    # Ekrana Uzun Basıldığında Dock Animasyonla Açılır ("basılı tutuğumuzda aşağıdaki dock açılacak")
    def _on_canvas_long_press(self, pos):
        print(f"[GenPen] Ekrana uzun basıldı: {pos.x()}, {pos.y()} -> Dock animasyonla açılıyor!")
        self.dock.slide_up_animated()

    def open_dock_animated(self):
        self.dock.slide_up_animated()

    def show_pin_dialog(self):
        dlg = PinDialog(self.pin_code, self)
        dlg.exec()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.resize(1280, 800)
        else:
            self.showFullScreen()

    def confirm_exit(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Gen Pen - Çıkış")
        msg.setText("<h2 style='color:#1A73E8; margin:0;'>Gen Pen Akıllı Tahta</h2><p style='font-size:14px; margin-top:8px;'>Uygulamayı kapatmak istediğinize emin misiniz?</p>")
        btn_exit = msg.addButton("Uygulamadan Çık", QMessageBox.ButtonRole.AcceptRole)
        btn_cancel = msg.addButton("İptal", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_cancel)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
            QLabel {
                font-size: 13px;
                color: #3C4043;
            }
            QPushButton {
                padding: 8px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-width: 90px;
            }
            QPushButton[text="Uygulamadan Çık"] {
                background-color: #D93025;
                color: white;
                border: none;
            }
            QPushButton[text="Uygulamadan Çık"]:hover {
                background-color: #B31412;
            }
            QPushButton[text="İptal"] {
                background-color: #F1F3F4;
                color: #3C4043;
                border: 1px solid #DADCE0;
            }
            QPushButton[text="İptal"]:hover {
                background-color: #E8EAED;
            }
        """)
        msg.exec()
        if msg.clickedButton() == btn_exit:
            print("[GenPen] Kullanıcı çıkış yaptı.")
            self.close()
            QApplication.quit()

    def _confirm_clear(self):
        reply = QMessageBox.question(self, "Tuvali Temizle", "Tüm çizimler ve eklenen resimler silinsin mi?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.dock.is_collapsed:
                self.dock.slide_up_animated()
            else:
                self.dock.slide_down_animated()
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Q and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.confirm_exit()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.dock.adjustSize()
        p_w = self.width()
        p_h = self.height()
        target_x = (p_w - self.dock.width()) // 2
        if not self.dock.is_collapsed:
            self.dock.move(target_x, p_h - self.dock.height() - 20)
        else:
            self.dock.move(target_x, p_h - self.dock.height() - 14)
        self.dock.raise_()

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.wait(1000)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("gen-pen")
    app.setApplicationDisplayName("Gen Pen")

    load_material_font()

    win = GenMainWindow()
    win.showFullScreen()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

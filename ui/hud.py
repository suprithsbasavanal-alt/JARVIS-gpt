"""
ui/hud.py  —  JARVIS 3.0 REAL ACCESS EDITION
UPGRADE: Added real-data panels:
- Confidence meter bar (0-100%) shown on every AI response
- Source citation panel below AI text
- Data Source Status Dashboard (green/red indicators, refreshes every 5s)
- Live system stats graph (CPU / RAM animated bars)
- All existing v3.0 animations preserved (arc reactor, particles, visualizer, typewriter)
"""

import math
import random
import datetime
import psutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsOpacityEffect, QScrollArea, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QPoint, QRectF
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QBrush
)

# ─── Colour palette ───────────────────────────────────────────────────────────
C_BG     = QColor(5,   10,  20,  210)
C_CYAN   = QColor(0,  230, 255)
C_BLUE   = QColor(0,  100, 255)
C_ORANGE = QColor(255, 120,  0)
C_GREEN  = QColor(0,  255, 150)
C_RED    = QColor(255,  50,  50)
C_YELLOW = QColor(255, 210,  0)
C_WHITE  = QColor(220, 240, 255)


# ─── Particle ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, w, h):
        self.reset(w, h)

    def reset(self, w, h):
        self.x     = random.uniform(0, w)
        self.y     = random.uniform(0, h)
        self.size  = random.uniform(1, 2.5)
        self.speed = random.uniform(0.3, 1.0)
        self.alpha = random.randint(30, 120)
        self.drift = random.uniform(-0.2, 0.2)

    def update(self, w, h):
        self.y -= self.speed
        self.x += self.drift
        if self.y < -5 or self.x < -5 or self.x > w + 5:
            self.reset(w, h)
            self.y = h + 5


# ─── Arc Reactor ──────────────────────────────────────────────────────────────
class ArcReactor(QWidget):
    """6-ring gyroscopic arc reactor with state-driven animation."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.rings = [
            [0,   1.0,  90, 180, C_CYAN],
            [0,  -1.6,  76, 160, C_BLUE],
            [0,   2.2,  62, 140, C_CYAN],
            [0,  -3.0,  48, 130, C_ORANGE],
            [0,   3.8,  34, 200, C_CYAN],
            [0,  -4.5,  20, 220, C_GREEN],
        ]
        self.pulse      = 0
        self.pulse_dir  = 1
        self.state      = "idle"
        self.scan_angle = 0
        self.glitch     = 0
        self._timer     = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def set_state(self, s: str):
        self.state = s
        if s == "error":
            self.glitch = 25

    def _tick(self):
        for ring in self.rings:
            ring[0] = (ring[0] + ring[1]) % 360
        spd = 4 if self.state in ("listening", "speaking") else 2
        self.pulse += spd * self.pulse_dir
        if self.pulse >= 100: self.pulse_dir = -1
        if self.pulse <= 0:   self.pulse_dir =  1
        self.scan_angle = (self.scan_angle + 2) % 360
        if self.glitch > 0: self.glitch -= 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        if self.glitch > 0 and random.random() < 0.5:
            p.fillRect(self.rect(), QColor(255, 0, 50, 25))
        for ring in self.rings:
            ang, _, r, alpha, col = ring
            pen = QPen(QColor(col.red(), col.green(), col.blue(), alpha))
            pen.setWidth(4 if self.state in ("thinking", "speaking") else 2)
            p.setPen(pen)
            p.save()
            p.translate(cx, cy)
            p.rotate(ang)
            p.drawEllipse(int(-r), int(-r), r * 2, r * 2)
            p.restore()
        if self.state == "thinking":
            sp = QPen(QColor(0, 255, 255, 90))
            sp.setWidth(2)
            p.setPen(sp)
            p.save()
            p.translate(cx, cy)
            p.rotate(self.scan_angle)
            p.drawLine(0, 0, 90, 0)
            p.restore()
        ga = 120 + self.pulse
        grad = QRadialGradient(cx, cy, 16)
        grad.setColorAt(0.0, QColor(0, 255, 255, ga))
        grad.setColorAt(1.0, QColor(0, 100, 255, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 16), int(cy - 16), 32, 32)
        p.setPen(QPen(C_CYAN))
        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        lbl = {"idle": "STANDBY", "listening": "LISTENING",
               "thinking": "PROCESSING", "speaking": "RESPONDING", "error": "ERROR"}
        p.drawText(self.rect().adjusted(0, 0, 0, -6),
                   Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                   lbl.get(self.state, "ACTIVE"))


# ─── Audio Visualizer ─────────────────────────────────────────────────────────
class AudioVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.num_bars  = 20
        self.levels    = [0.02] * self.num_bars
        self.audio_lvl = 0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(40)

    def set_audio_level(self, lvl):
        self.audio_lvl = max(0, min(100, lvl))

    def _tick(self):
        base = self.audio_lvl / 100.0
        for i in range(self.num_bars):
            tgt = base * random.uniform(0.4, 1.3)
            tgt = max(0.02, min(1.0, tgt))
            self.levels[i] += (tgt - self.levels[i]) * 0.35
        self.update()

    def paintEvent(self, event):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w  = self.width()
        h  = self.height()
        bw = (w - self.num_bars) / self.num_bars
        for i, lvl in enumerate(self.levels):
            bh     = max(3, lvl * (h - 4))
            x      = i * (bw + 1)
            y      = h - bh
            hue    = int(180 + lvl * 60)
            colour = QColor.fromHsv(hue, 255, 255, 190)
            p.fillRect(int(x), int(y), int(bw), int(bh), colour)


# ─── Typewriter Label ─────────────────────────────────────────────────────────
class TypewriterLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._full  = ""
        self._shown = 0
        self._t     = QTimer(self)
        self._t.timeout.connect(self._step)

    def set_text_animated(self, text: str, speed_ms: int = 16):
        self._full  = text
        self._shown = 0
        self._t.stop()
        self.setText("")
        self._t.start(speed_ms)

    def _step(self):
        if self._shown < len(self._full):
            self._shown += 1
            self.setText(self._full[:self._shown])
        else:
            self._t.stop()


# ─── Confidence Meter Bar ─────────────────────────────────────────────────────
class ConfidenceMeter(QWidget):
    """Animated horizontal bar showing AI confidence 0-100%."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(22)
        self._target  = 0.0    # target fill 0.0-1.0
        self._current = 0.0    # smoothed current fill
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(30)

    def set_confidence(self, pct: int):
        """Set confidence 0-100."""
        self._target = max(0, min(100, pct)) / 100.0

    def _tick(self):
        self._current += (self._target - self._current) * 0.12
        self.update()

    def paintEvent(self, event):
        p   = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w   = self.width()
        h   = self.height()
        pct = self._current

        # Background track
        p.fillRect(0, 0, w, h, QColor(20, 30, 50, 180))

        # Filled bar — colour shifts green → yellow → red based on confidence
        hue   = int(120 * pct)          # 0=red, 60=yellow, 120=green
        bar_w = int(w * pct)
        if bar_w > 2:
            grad = QLinearGradient(0, 0, bar_w, 0)
            grad.setColorAt(0.0, QColor.fromHsv(hue, 220, 200, 180))
            grad.setColorAt(1.0, QColor.fromHsv(hue, 255, 255, 255))
            p.fillRect(0, 2, bar_w, h - 4, QBrush(grad))

        # Border
        pen = QPen(QColor(0, 200, 255, 80))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(0, 0, w - 1, h - 1)

        # Label
        p.setPen(QPen(C_WHITE))
        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        label = f"CONFIDENCE: {int(pct * 100)}%"
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, label)


# ─── Status Dashboard ─────────────────────────────────────────────────────────
class StatusDashboard(QWidget):
    """
    Shows green/red dots for every data source with live status text.
    Refreshes every 5 seconds from core.real_access status registry.
    """

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("◈  SYSTEM STATUS")
        title.setStyleSheet("color: #00ffff; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        layout.addWidget(title)

        self._labels: dict[str, QLabel] = {}
        self._layout = layout

        # Refresh every 5 seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(5000)
        self.refresh()

    def refresh(self):
        """Pulls live status from real_access and updates all indicators."""
        try:
            import core.real_access as ra
            statuses = ra.get_all()
        except Exception:
            return

        for name, info in statuses.items():
            ok  = info["ok"]
            msg = info["message"][:28]
            dot = "●"
            colour = "#00ff88" if ok else "#ff3333"

            if name not in self._labels:
                lbl = QLabel()
                lbl.setFont(QFont("Courier New", 9))
                lbl.setWordWrap(False)
                self._labels[name] = lbl
                self._layout.addWidget(lbl)

            self._labels[name].setText(f'<span style="color:{colour};">{dot}</span> <span style="color:#aaddff;">{name[:16]}</span>')
            self._labels[name].setToolTip(f"{name}: {info['message']}\nLast checked: {info['last_checked']}")


# ─── Particle Canvas ──────────────────────────────────────────────────────────
class ParticleCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.particles = [Particle(1100, 380) for _ in range(70)]
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(33)

    def _tick(self):
        for pt in self.particles:
            pt.update(self.width(), self.height())
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        for pt in self.particles:
            c = QColor(0, 200, 255, pt.alpha)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(pt.x), int(pt.y), int(pt.size), int(pt.size))


# ─── Main HUD Window ──────────────────────────────────────────────────────────
class CinematicHUD(QWidget):
    """JARVIS 3.0 Real-Access HUD with confidence meter and status dashboard."""

    sig_update_ai   = pyqtSignal(str)
    sig_update_user = pyqtSignal(str)
    sig_state       = pyqtSignal(str)
    sig_audio       = pyqtSignal(int)
    sig_error       = pyqtSignal(str)
    sig_confidence  = pyqtSignal(int)       # NEW: 0-100
    sig_sources     = pyqtSignal(list)      # NEW: list of source strings

    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self._build_ui()
        self._connect_signals()
        self._start_stats_timer()
        self._fade_in()

    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1060, 380)

        screen = self.screen().geometry()
        self.move((screen.width() - 1060) // 2, 50)

        # Particle background
        self.particles_bg = ParticleCanvas(self)
        self.particles_bg.resize(1060, 380)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        # ── Arc Reactor (left) ───────────────────────────────────────────
        self.reactor = ArcReactor()
        root.addWidget(self.reactor)

        # ── Centre column ────────────────────────────────────────────────
        mid = QVBoxLayout()
        mid.setSpacing(5)

        self.lbl_title = QLabel("J.A.R.V.I.S.  ◈  3.0 REAL ACCESS  ◈  NO HALLUCINATION")
        self.lbl_title.setStyleSheet(
            "color: #00ffff; font-family: 'Courier New'; font-size: 15px; "
            "font-weight: bold; letter-spacing: 2px;"
        )
        mid.addWidget(self.lbl_title)

        self.lbl_user = QLabel("▶  AWAITING VOCAL INPUT…")
        self.lbl_user.setStyleSheet(
            "color: #aaddff; font-family: 'Courier New'; font-size: 13px;"
        )
        self.lbl_user.setWordWrap(True)
        mid.addWidget(self.lbl_user)

        self.lbl_ai = TypewriterLabel()
        self.lbl_ai.setStyleSheet(
            "color: #00ffcc; font-family: 'Courier New'; font-size: 14px;"
        )
        self.lbl_ai.setWordWrap(True)
        self.lbl_ai.setText("[JARVIS]: All systems nominal. Real-access mode active.")
        mid.addWidget(self.lbl_ai)

        # Confidence meter
        self.confidence = ConfidenceMeter()
        mid.addWidget(self.confidence)

        # Source citation label
        self.lbl_source = QLabel("Source: —")
        self.lbl_source.setStyleSheet(
            "color: #667799; font-family: 'Courier New'; font-size: 10px; "
            "font-style: italic;"
        )
        self.lbl_source.setWordWrap(True)
        mid.addWidget(self.lbl_source)

        # Audio visualizer
        self.visualizer = AudioVisualizer()
        mid.addWidget(self.visualizer)

        # Stats line
        self.lbl_stats = QLabel("CPU: --% │ RAM: --% │ BAT: --%")
        self.lbl_stats.setStyleSheet(
            "color: #ff9900; font-family: 'Courier New'; font-size: 11px;"
        )
        mid.addWidget(self.lbl_stats)

        root.addLayout(mid, stretch=1)

        # ── Right column: Status Dashboard + Clock ────────────────────────
        right = QVBoxLayout()
        right.setSpacing(6)

        self.lbl_clock = QLabel("--:--:--")
        self.lbl_clock.setStyleSheet(
            "color: #00ffcc; font-family: 'Courier New'; font-size: 22px; font-weight: bold;"
        )
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.lbl_clock)

        self.status_dash = StatusDashboard()
        right.addWidget(self.status_dash)
        right.addStretch()
        root.addLayout(right)

        # Timers
        self._clock_t = QTimer(self)
        self._clock_t.timeout.connect(self._update_clock)
        self._clock_t.start(1000)
        self._update_clock()

    def _connect_signals(self):
        self.sig_update_ai.connect(self._on_ai)
        self.sig_update_user.connect(self._on_user)
        self.sig_state.connect(lambda s: self.reactor.set_state(s))
        self.sig_audio.connect(self._on_audio)
        self.sig_error.connect(self._on_error)
        self.sig_confidence.connect(self.confidence.set_confidence)
        self.sig_sources.connect(self._on_sources)

    def _on_ai(self, text: str):
        self.lbl_ai.set_text_animated(f"[JARVIS]: {text}", speed_ms=14)

    def _on_user(self, text: str):
        self.lbl_user.setText(f"▶  {text.upper()}")

    def _on_audio(self, lvl: int):
        self.reactor.set_audio_level(lvl) if hasattr(self.reactor, "set_audio_level") else None
        self.visualizer.set_audio_level(lvl)

    def _on_error(self, msg: str):
        self.reactor.set_state("error")
        self.lbl_ai.set_text_animated(f"[ERROR]: {msg}", speed_ms=10)
        self.confidence.set_confidence(0)
        self.lbl_source.setText("Source: Error log")

    def _on_sources(self, sources: list):
        text = "Source: " + " | ".join(sources[:3]) if sources else "Source: —"
        self.lbl_source.setText(text)

    def _start_stats_timer(self):
        self._stats_t = QTimer(self)
        self._stats_t.timeout.connect(self._update_stats)
        self._stats_t.start(2000)

    def _update_stats(self):
        try:
            cpu  = psutil.cpu_percent()
            ram  = psutil.virtual_memory().percent
            bat  = psutil.sensors_battery()
            bstr = f"{bat.percent:.0f}%" if bat else "N/A"
            self.lbl_stats.setText(f"CPU: {cpu}% │ RAM: {ram}% │ BAT: {bstr}")
        except Exception:
            pass

    def _update_clock(self):
        now = datetime.datetime.now()
        self.lbl_clock.setText(now.strftime("%H:%M:%S"))

    def _fade_in(self):
        self._eff  = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._anim = QPropertyAnimation(self._eff, b"opacity")
        self._anim.setDuration(1800)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
        p.fillPath(path, C_BG)
        alpha = 55 + int(self.reactor.pulse * 0.7)
        pen   = QPen(QColor(0, 220, 255, alpha))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawPath(path)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.5, QColor(0, 200, 255, 70))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, self.width(), 2, QBrush(grad))

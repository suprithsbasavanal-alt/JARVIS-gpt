"""
ui/hud.py
Cinematic Next-Generation HUD for JARVIS.
Features OpenGL-like rendering, continuous 60FPS animations, and glassmorphism.
"""
import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath

class ArcReactor(QWidget):
    """Futuristic Rotating Radar/Arc Reactor Animation"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        # 60 FPS smooth animation loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def update_animation(self):
        self.angle = (self.angle + 2) % 360
        self.pulse += 3 * self.pulse_dir
        if self.pulse > 100:
            self.pulse_dir = -1
        elif self.pulse < 0:
            self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Outer Glowing Ring
        pen = QPen(QColor(0, 200, 255, 100 + self.pulse))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(10, 10, 180, 180)
        
        # Inner Rotating Arc
        pen.setColor(QColor(0, 255, 255, 200))
        pen.setWidth(6)
        painter.setPen(pen)
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        painter.drawArc(-70, -70, 140, 140, 0, 180 * 16)
        
        # Counter-Rotating Core
        painter.rotate(-self.angle * 2.5) 
        pen.setColor(QColor(255, 100, 0, 180)) # Orange accent
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawArc(-50, -50, 100, 100, 90 * 16, 270 * 16)


class CinematicHUD(QWidget):
    """Main Glassmorphism UI Overlay"""
    sig_update_ai = pyqtSignal(str)
    sig_update_user = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_stats_timer()

    def init_ui(self):
        # Frameless, transparent, always on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(850, 300)
        
        # Center top alignment
        screen = self.screen().geometry()
        self.move((screen.width() - 850) // 2, 80)
        
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Left: Arc Reactor Animation
        self.arc = ArcReactor()
        self.layout.addWidget(self.arc, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Right: Data Console
        self.data_layout = QVBoxLayout()
        
        self.lbl_title = QLabel("J.A.R.V.I.S. // CORE SYSTEM ONLINE")
        self.lbl_title.setStyleSheet("color: #00ffff; font-family: 'Courier New'; font-size: 24px; font-weight: bold; letter-spacing: 2px;")
        self.data_layout.addWidget(self.lbl_title)
        
        self.lbl_user = QLabel("> AWAITING VOCAL INPUT...")
        self.lbl_user.setStyleSheet("color: #ffffff; font-family: 'Courier New'; font-size: 16px; opacity: 0.8;")
        self.data_layout.addWidget(self.lbl_user)
        
        self.lbl_ai = QLabel("[AI]: System initialization complete. Ready for directives.")
        self.lbl_ai.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 18px;")
        self.lbl_ai.setWordWrap(True)
        self.data_layout.addWidget(self.lbl_ai)
        
        self.lbl_stats = QLabel("SYS.DIAGNOSTICS -> CPU: 0% | MEMORY: 0%")
        self.lbl_stats.setStyleSheet("color: #ff9900; font-family: 'Courier New'; font-size: 14px; margin-top: 20px;")
        self.data_layout.addWidget(self.lbl_stats)
        
        self.layout.addLayout(self.data_layout)
        
        # Signal Connections
        self.sig_update_ai.connect(self.set_ai_text)
        self.sig_update_user.connect(self.set_user_text)

        # Entrance Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1500)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def set_user_text(self, text):
        self.lbl_user.setText(f"> {text.upper()}")

    def set_ai_text(self, text):
        self.lbl_ai.setText(f"[AI]: {text}")

    def init_stats_timer(self):
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)
        
    def update_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.lbl_stats.setText(f"SYS.DIAGNOSTICS -> CPU: {cpu}% | MEMORY: {ram}%")
        except:
            pass

    # Allow dragging the HUD
    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self.oldPos
        self.move(self.pos() + delta)
        self.oldPos = event.globalPosition().toPoint()

    def paintEvent(self, event):
        # Draw Glassmorphism Background Panel
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        # Semi-transparent dark background
        painter.fillPath(path, QColor(10, 15, 30, 180))
        
        # Neon Border
        pen = QPen(QColor(0, 255, 255, 80))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

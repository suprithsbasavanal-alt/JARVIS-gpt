"""
ui/hud.py
Builds the futuristic, transparent, Iron-Man-style GUI using PyQt6.
"""
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
import system.monitor as monitor

class JarvisHUD(QWidget):
    # Signals to update UI from background threads safely
    sig_update_user = pyqtSignal(str)
    sig_update_ai = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.old_pos = self.pos()
        self.init_ui()
        
        # Connect signals
        self.sig_update_user.connect(self.set_user_text)
        self.sig_update_ai.connect(self.set_ai_text)

    def init_ui(self):
        # Window settings: frameless, always on top, transparent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 500)
        
        main_layout = QVBoxLayout()
        
        # The main dark panel representing the HUD
        self.panel = QWidget()
        self.panel.setStyleSheet("""
            QWidget {
                background-color: rgba(5, 10, 20, 230);
                border: 2px solid #00f3ff;
                border-radius: 15px;
            }
        """)
        panel_layout = QVBoxLayout(self.panel)
        
        # Title
        self.title = QLabel("J.A.R.V.I.S. SYSTEM ONLINE")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #00f3ff; font-family: 'Courier New'; font-size: 20px; font-weight: bold; border: none;")
        panel_layout.addWidget(self.title)
        
        # Voice Wave Animation Placeholder
        self.wave_label = QLabel("— — — — — — — —")
        self.wave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wave_label.setStyleSheet("color: #00f3ff; font-size: 18px; border: none; letter-spacing: 5px;")
        panel_layout.addWidget(self.wave_label)
        
        # System Stats Layout
        stats_layout = QVBoxLayout()
        
        # CPU Bar
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet("color: #00ffcc; font-size: 10px; border: none;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setStyleSheet("QProgressBar { border: 1px solid #00ffcc; border-radius: 3px; background-color: transparent; } QProgressBar::chunk { background-color: #00ffcc; }")
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(5)
        stats_layout.addWidget(self.cpu_label)
        stats_layout.addWidget(self.cpu_bar)
        
        # RAM Bar
        self.ram_label = QLabel("RAM: 0% | BATT: 100%")
        self.ram_label.setStyleSheet("color: #00ffcc; font-size: 10px; border: none;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setStyleSheet("QProgressBar { border: 1px solid #00ffcc; border-radius: 3px; background-color: transparent; } QProgressBar::chunk { background-color: #00ffcc; }")
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setFixedHeight(5)
        stats_layout.addWidget(self.ram_label)
        stats_layout.addWidget(self.ram_bar)
        
        panel_layout.addLayout(stats_layout)
        
        # Spacer
        panel_layout.addSpacing(15)
        
        # Chat History
        self.user_text = QLabel("User: [Standing By]")
        self.user_text.setWordWrap(True)
        self.user_text.setStyleSheet("color: #aaaaaa; font-family: Arial; font-size: 13px; border: none;")
        panel_layout.addWidget(self.user_text)
        
        self.ai_text = QLabel("JARVIS: Systems initialized and ready.")
        self.ai_text.setWordWrap(True)
        self.ai_text.setStyleSheet("color: #ffffff; font-family: Arial; font-size: 14px; font-weight: bold; border: none;")
        panel_layout.addWidget(self.ai_text)
        
        # Spacer
        panel_layout.addStretch()
        
        main_layout.addWidget(self.panel)
        self.setLayout(main_layout)
        
        # Timers for updates
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000) # Update system stats every 2 seconds
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_wave)
        self.anim_timer.start(150)
        self.anim_step = 0

    def update_stats(self):
        """Fetches latest system stats and updates the progress bars."""
        stats = monitor.get_system_stats()
        self.cpu_label.setText(f"CPU: {stats['cpu']}%")
        self.cpu_bar.setValue(int(stats['cpu']))
        self.ram_label.setText(f"RAM: {stats['ram']}% | BATT: {stats['battery']}%")
        self.ram_bar.setValue(int(stats['ram']))

    def animate_wave(self):
        """Simple text-based animation to simulate a voice wave."""
        frames = [
            "  —   —   —   —  ",
            "  |   |   |   |  ",
            " ||| ||| ||| ||| ",
            "  |   |   |   |  "
        ]
        self.wave_label.setText(frames[self.anim_step % len(frames)])
        self.anim_step += 1

    def set_user_text(self, text):
        self.user_text.setText(f"User: {text}")

    def set_ai_text(self, text):
        self.ai_text.setText(f"JARVIS: {text}")

    # Allow dragging the window with the mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

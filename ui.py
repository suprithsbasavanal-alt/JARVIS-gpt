"""
ui.py
This file builds the futuristic graphical user interface (GUI) using PyQt6.
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QFont

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class JarvisUI(QWidget):
    # Signals to communicate between background threads and the main GUI thread
    update_ai_text_signal = pyqtSignal(str)
    update_user_text_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.old_pos = self.pos()
        
        # Connect signals to their update functions
        self.update_ai_text_signal.connect(self.set_ai_text)
        self.update_user_text_signal.connect(self.set_user_text)

    def init_ui(self):
        """Sets up the visual elements of the window."""
        try:
            # Make the window frameless and always on top
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            # Make the background semi-transparent
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
            # Set window size
            self.resize(350, 450)
            
            # Main layout
            layout = QVBoxLayout()
            
            # Create the dark background widget with rounded corners and neon borders
            self.bg_widget = QWidget()
            self.bg_widget.setStyleSheet('''
                QWidget {
                    background-color: rgba(10, 15, 30, 230);
                    border: 2px solid #00f3ff;
                    border-radius: 20px;
                }
            ''')
            bg_layout = QVBoxLayout(self.bg_widget)
            
            # Title Label (Sci-fi style)
            self.title_label = QLabel("J.A.R.V.I.S.")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setStyleSheet('color: #00f3ff; font-size: 28px; font-weight: bold; border: none;')
            bg_layout.addWidget(self.title_label)
            
            # Memory Panel
            self.memory_panel = QLabel("Memory System Active | Syncing...")
            self.memory_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.memory_panel.setStyleSheet('color: #00ff00; font-size: 10px; border: none; padding: 2px;')
            bg_layout.addWidget(self.memory_panel)
            
            # Pulse/Wave Visual (Simple text based animation for beginners)
            self.wave_label = QLabel("|||||||||||||||||||||")
            self.wave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.wave_label.setStyleSheet('color: #00f3ff; font-size: 16px; border: none;')
            bg_layout.addWidget(self.wave_label)
            
            # User Speech Label (What I said)
            self.user_label = QLabel("You: ...")
            self.user_label.setWordWrap(True)
            self.user_label.setStyleSheet('color: #a0a0a0; font-size: 14px; border: none; padding: 10px; background-color: rgba(255,255,255,10); border-radius: 10px;')
            bg_layout.addWidget(self.user_label)
            
            # AI Speech Label (What Jarvis said)
            self.ai_label = QLabel("Jarvis: Waiting for wake word...")
            self.ai_label.setWordWrap(True)
            self.ai_label.setStyleSheet('color: #ffffff; font-size: 15px; font-weight: bold; border: none; padding: 10px; background-color: rgba(0, 243, 255, 20); border-radius: 10px;')
            bg_layout.addWidget(self.ai_label)
            
            # Settings Button
            self.settings_btn = QPushButton("Settings")
            self.settings_btn.setStyleSheet('color: #00f3ff; background-color: transparent; border: 1px solid #00f3ff; border-radius: 5px; padding: 5px;')
            bg_layout.addWidget(self.settings_btn)
            
            # Time Label
            self.time_label = QLabel()
            self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.time_label.setStyleSheet('color: #00f3ff; font-size: 12px; border: none; margin-top: 10px;')
            bg_layout.addWidget(self.time_label)
            
            # Add the background widget to the main layout
            layout.addWidget(self.bg_widget)
            self.setLayout(layout)
            
            # Set up a timer to update the clock every second
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)
            self.update_time()
            
            # Timer for simple wave animation
            self.wave_timer = QTimer(self)
            self.wave_timer.timeout.connect(self.animate_wave)
            self.wave_timer.start(200)
            self.wave_state = 0
            
        except Exception as e:
            logging.error(f"Error setting up UI: {e}")

    def update_time(self):
        """Updates the time label with the current date and time."""
        import datetime
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
        
    def animate_wave(self):
        """Creates a simple text-based pulsing wave animation."""
        waves = [
            "|||||||||||||||||||||",
            " | | | | | | | | | | ",
            "  ||  ||  ||  ||  || ",
            " |  |  |  |  |  |  | "
        ]
        self.wave_label.setText(waves[self.wave_state])
        self.wave_state = (self.wave_state + 1) % len(waves)
        
    def set_user_text(self, text):
        """Updates the label showing what the user said."""
        self.user_label.setText(f"You: {text}")
        
    def set_ai_text(self, text):
        """Updates the label showing what Jarvis said."""
        self.ai_label.setText(f"Jarvis: {text}")

    # The following three methods allow the frameless window to be dragged by the mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

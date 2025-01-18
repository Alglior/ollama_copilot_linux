import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGroupBox, QTextEdit, QLineEdit, QPushButton, QComboBox, QFrame
from PyQt5.QtCore import Qt

# Global application style
GLOBAL_STYLE = """
    QLabel, QTextEdit, QLineEdit, QPushButton, QComboBox {
        font-size: 12pt;
    }
    QGroupBox {
        font-size: 12pt;
        font-weight: bold;
        border: 2px solid #666;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        padding: 0 5px;
    }
"""

# Welcome box style
WELCOME_BOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 2px solid #666;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        padding: 0 5px;
    }
"""

# Suggestions box style
SUGGESTIONS_BOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 2px solid #666;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        padding: 0 5px;
    }
    QPushButton {
        text-align: left;
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: 3px;
        background-color: #f8f9fa;
    }
    QPushButton:hover {
        background-color: #e9ecef;
    }
"""

# Chat display style
CHAT_DISPLAY_STYLE = """
    QTextEdit {
        font-family: Arial, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
    }
    pre {
        background-color: #f6f8fa;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 16px;
        overflow-x: auto;
        font-family: 'Courier New', Courier, monospace;
    }
    code {
        background-color: #f6f8fa;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: 'Courier New', Courier, monospace;
    }
"""

# Loading overlay style
LOADING_OVERLAY_STYLE = """
    QFrame {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 10px;
    }
    QLabel {
        color: #4a90e2;
        font-size: 14pt;
        font-weight: bold;
    }
"""

# Message box styles
USER_MESSAGE_STYLE = """
    QGroupBox {
        background-color: #f8f9fa;
        border: none;
        border-radius: 8px;
        margin: 0;
        padding: 0;
    }
    QGroupBox::title {
        border: none;
        margin: 0;
        padding: 0;
        background: none;
        subcontrol-origin: none;
        subcontrol-position: none;
    }
    QGroupBox::indicator {
        width: 0;
        height: 0;
        padding: 0;
        margin: 0;
    }
"""

AI_MESSAGE_STYLE = """
    QGroupBox {
        background-color: #f0f7ff;
        border: none;
        border-radius: 8px;
        margin: 0;
        padding: 0;
    }
    QGroupBox::title {
        border: none;
        margin: 0;
        padding: 0;
        background: none;
        subcontrol-origin: none;
        subcontrol-position: none;
    }
    QGroupBox::indicator {
        width: 0;
        height: 0;
        padding: 0;
        margin: 0;
    }
"""

STOP_BUTTON_STYLE = """
    QPushButton {
        background-color: #ff4444;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: #ff6666;
    }
    QPushButton:disabled {
        background-color: #cccccc;
    }
"""

RELOAD_BUTTON_STYLE = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""

SYSTEM_MESSAGE_STYLE = """
    QGroupBox {
        background-color: #fff3cd;
        border: none;
        border-radius: 8px;
        margin: 0;
        padding: 0;
    }
"""

REFRESH_BUTTON_STYLE = """
    QPushButton {
        font-size: 15pt;
        font-weight: bold;
        border: none;
        border-radius: 12px;
        background-color: transparent;
    }
    QPushButton:hover {
        background-color: #e9ecef;
    }
"""

DISABLED_INPUT_STYLE = "background-color: #e9e9e9;"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.welcome_box = QGroupBox("Welcome")
        self.welcome_box.setStyleSheet(WELCOME_BOX_STYLE)
        self.layout.addWidget(self.welcome_box)

        self.suggestions_box = QGroupBox("Suggestions")
        self.suggestions_box.setStyleSheet(SUGGESTIONS_BOX_STYLE)
        self.layout.addWidget(self.suggestions_box)

        self.chat_display = QTextEdit()
        self.chat_display.setStyleSheet(CHAT_DISPLAY_STYLE)
        self.layout.addWidget(self.chat_display)

        self.loading_overlay = QFrame(self.central_widget)
        self.loading_overlay.setStyleSheet(LOADING_OVERLAY_STYLE)
        self.loading_overlay.setGeometry(0, 0, 800, 600)
        self.loading_overlay.setVisible(False)
        self.layout.addWidget(self.loading_overlay)

        self.setStyleSheet(GLOBAL_STYLE)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

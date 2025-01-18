from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QTextEdit, QLineEdit, QPushButton,
                             QComboBox, QHBoxLayout, QGroupBox, QLabel,
                             QProgressDialog, QDialog, QFrame)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal
# Explicitly import each QtGui component
from PySide6.QtGui import (QPainter,  # Add this explicit import
                          QColor,
                          QRadialGradient,
                          QPen,
                          QTextCursor)  # Add QTextCursor import
import sys
import requests
import json
import os
import random
import threading
import markdown2  # Replace markdown with markdown2 for better HTML conversion
# Add this import at the top with other imports
from styles import (GLOBAL_STYLE, WELCOME_BOX_STYLE, SUGGESTIONS_BOX_STYLE,
                   CHAT_DISPLAY_STYLE, LOADING_OVERLAY_STYLE, USER_MESSAGE_STYLE,
                   AI_MESSAGE_STYLE, STOP_BUTTON_STYLE, RELOAD_BUTTON_STYLE,
                   SYSTEM_MESSAGE_STYLE, REFRESH_BUTTON_STYLE, DISABLED_INPUT_STYLE)
from PySide6.QtWidgets import QScrollArea

class QProgressIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16)  # ~60 FPS for smoother animation
        self.setFixedSize(96, 96)  # Even bigger size
        self.opacity = 1.0

    def rotate(self):
        self.angle = (self.angle + 5) % 360  # Smaller increments for smoother rotation
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center point
        center = self.rect().center()
        size = min(self.width(), self.height()) - 4
        
        # Create gradient for glowing effect
        gradient = QRadialGradient(center, size/2)
        color = QColor('#4a90e2')
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(150))
        
        # Draw glowing circle segments
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        
        rect = self.rect()
        rect.adjust(2, 2, -2, -2)
        
        # Draw 3 arcs with different opacities
        for i in range(3):
            painter.setOpacity(1.0 - (i * 0.3))
            span = 120 - (i * 30)  # Decreasing span for trailing effect
            painter.drawPie(rect, (self.angle - i * 10) * 16, span * 16)

# Add new worker class for async reload
class ReloadWorker(QThread):
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        if not self._is_running:
            return
        try:
            # First copy the model to unload it from memory
            requests.post('http://localhost:11434/api/copy',
                        json={"source": self.model_name, "destination": self.model_name})
            
            # Create a new session to force model reload
            requests.post('http://localhost:11434/api/generate',
                        json={
                            "model": self.model_name,
                            "prompt": "test",
                            "stream": False
                        })
            self.finished.emit()
        except requests.exceptions.RequestException:
            self.error.emit("Cannot connect to Ollama service")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_prompt = None  # Add this line to store the original message
        self.reload_worker = None
        self.current_ai_labels = {}  # Add this line to store AI message labels
        # Add system prompt constant at the start of the class
        self.SYSTEM_PROMPT = """You are a highly experienced Linux system administrator and expert.
Your role is to:
- Provide accurate and detailed explanations of Linux commands, concepts, and best practices
- Give practical examples and use cases
- Explain security implications when relevant
- Recommend modern and efficient solutions
- Help users understand Linux system internals
- Share professional tips and common pitfalls to avoid
Be concise but thorough in your responses."""

        # Load Linux prompts from file
        self.linux_prompts = []
        try:
            prompts_file = os.path.join(os.path.dirname(__file__), 'linux_prompts.txt')
            with open(prompts_file, 'r') as f:
                self.linux_prompts = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading prompts: {e}")
            # Fallback to empty list if file can't be loaded
            self.linux_prompts = []

        self.setWindowTitle("Ollama Chat")
        self.settings_file = os.path.expanduser("~/.ollama_chat_settings.json")
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.25)  # 25% of screen width
        self.setGeometry(0, 0, width, screen.height())
        
        # Set global font size for the application
        self.setStyleSheet(GLOBAL_STYLE)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create model control container
        model_container = QWidget()
        model_container_layout = QVBoxLayout(model_container)
        
        # Add model selector and buttons
        model_layout = QHBoxLayout()
        self.model_selector = QComboBox()
        self.refresh_button = QPushButton("Refresh Models")
        self.set_default_button = QPushButton("Set as Default")
        self.reload_button = QPushButton("Reload Model")
        self.progress_indicator = QProgressIndicator()
        self.progress_indicator.hide()  # Hidden by default
        
        self.refresh_button.clicked.connect(self.fetch_models)
        self.set_default_button.clicked.connect(self.set_default_model)
        self.reload_button.clicked.connect(self.reload_model)
        
        model_layout.addWidget(self.model_selector)
        model_layout.addWidget(self.refresh_button)
        model_layout.addWidget(self.set_default_button)
        model_layout.addWidget(self.reload_button)
        model_layout.addWidget(self.progress_indicator)
        
        model_container_layout.addLayout(model_layout)
        layout.addWidget(model_container)
        
        # Create welcome box
        welcome_box = QGroupBox("Welcome to Ollama Linux Chat")
        welcome_box.setStyleSheet(WELCOME_BOX_STYLE)
        welcome_layout = QVBoxLayout()
        welcome_text = QLabel("""
• Ask any Linux-related questions
• Get help with commands and system management
• Learn about Linux concepts and best practices

Start by typing your question below or choose from the suggestions.""")
        welcome_text.setWordWrap(True)
        welcome_layout.addWidget(welcome_text)
        welcome_box.setLayout(welcome_layout)
        layout.addWidget(welcome_box)

        # Create suggestions box with custom title widget
        suggestions_box = QGroupBox()
        suggestions_box.setStyleSheet(SUGGESTIONS_BOX_STYLE)
        suggestions_layout = QVBoxLayout()
        
        # Create title widget with refresh button
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("Example Questions")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        refresh_button = QPushButton("⟳")  # Using unicode refresh symbol
        refresh_button.setFixedSize(25, 25)
        refresh_button.setStyleSheet(REFRESH_BUTTON_STYLE)
        refresh_button.clicked.connect(self.refresh_suggestions)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(refresh_button)
        title_layout.addStretch()
        
        suggestions_layout.addWidget(title_widget)
        
        # Create buttons for random suggestions
        for prompt in random.sample(self.linux_prompts, 3):
            suggestion_button = QPushButton(prompt)
            suggestion_button.clicked.connect(lambda checked, p=prompt: self.use_suggestion(p))
            suggestions_layout.addWidget(suggestion_button)
        
        suggestions_box.setLayout(suggestions_layout)
        layout.addWidget(suggestions_box)

        # Replace chat display with scroll area and widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide vertical scrollbar
        scroll_container = QWidget()
        self.chat_layout = QVBoxLayout(scroll_container)
        self.chat_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        layout.addWidget(scroll_area)
        
        # Initialize loading overlay right after chat display
        self.loading_overlay = QFrame(scroll_container)
        self.loading_overlay.setStyleSheet(LOADING_OVERLAY_STYLE)
        
        # Create overlay layout
        overlay_layout = QVBoxLayout(self.loading_overlay)
        
        # Create centered progress indicator
        self.center_progress = QProgressIndicator(self.loading_overlay)
        overlay_layout.addWidget(self.center_progress, 0, Qt.AlignCenter)
        
        # Add loading text
        self.loading_label = QLabel("Reloading Model...", self.loading_overlay)
        self.loading_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(self.loading_label, 0, Qt.AlignCenter)
        
        self.loading_overlay.hide()

        # Create input field with random placeholder
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("type here or choose a suggestion")
        self.input_field.returnPressed.connect(self.send_message)
        layout.addWidget(self.input_field)
        
        # Create button layout (remove refresh suggestions button from here)
        button_layout = QHBoxLayout()
        
        # Create send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        # Add stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.setEnabled(False)
        
        # Create clear button
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        # Add generation control flag
        self.is_generating = False
        self.should_stop = False
        
        self.move(0, 0)
        
        # Fetch models when starting
        self.fetch_models()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Cleanup threads before destruction"""
        if self.reload_worker:
            self.reload_worker.stop()
            self.reload_worker.wait()
            self.reload_worker = None

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('default_model')
        except Exception:
            return None
        return None

    def save_settings(self, model):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({'default_model': model}, f)
        except Exception as e:
            self.display_system_message(f"Error saving settings: {str(e)}")

    def display_system_message(self, message):
        """Display a system message in the chat layout"""
        system_box = QGroupBox()
        system_box.setStyleSheet(SYSTEM_MESSAGE_STYLE)
        
        box_layout = QVBoxLayout(system_box)
        box_layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel(message)
        label.setWordWrap(True)
        box_layout.addWidget(label)
        
        self.chat_layout.addWidget(system_box)
        
        # Scroll to bottom after adding system message
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().maximum()
            )

    def set_default_model(self):
        current_model = self.model_selector.currentText()
        if current_model:
            self.save_settings(current_model)
            self.display_system_message(f"Set {current_model} as default model")

    def fetch_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                models = response.json()['models']
                current_model = self.model_selector.currentText()
                self.model_selector.clear()
                default_model = self.load_settings()
                default_index = 0
                
                for i, model in enumerate(models):
                    self.model_selector.addItem(model['name'])
                    if default_model and model['name'] == default_model:
                        default_index = i
                    # Keep the previously selected model if it exists
                    elif current_model and model['name'] == current_model:
                        default_index = i
                
                self.model_selector.setCurrentIndex(default_index)
            else:
                self.display_system_message("Error: Failed to fetch models")
        except requests.exceptions.RequestException:
            self.display_system_message("Error: Cannot connect to Ollama service")

    def stop_generation(self):
        """Stop the current generation"""
        self.should_stop = True
        self.stop_button.setEnabled(False)
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)

    def disable_input(self):
        """Disable input controls"""
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.input_field.setStyleSheet(DISABLED_INPUT_STYLE)
        
    def enable_input(self):
        """Enable input controls"""
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setStyleSheet("")

    def create_message_box(self, is_user, message):
        box = QGroupBox()
        box.setStyleSheet(USER_MESSAGE_STYLE if is_user else AI_MESSAGE_STYLE)
        
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 10, 10, 10)
        box_layout.setSpacing(5)  # Added spacing between elements
        
        # Create header layout for the role label and stop button
        header_layout = QHBoxLayout()
        role_label = QLabel("<b>You</b>" if is_user else "<b>AI:</b>")
        header_layout.addWidget(role_label)
        
        if not is_user:
            # Create button container for better alignment
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setSpacing(5)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            # Stop button
            stop_button = QPushButton("Stop")
            stop_button.setFixedSize(60, 25)
            stop_button.setStyleSheet(STOP_BUTTON_STYLE)
            stop_button.clicked.connect(self.stop_generation)
            stop_button.setEnabled(False)
            self.stop_button = stop_button
            
            # Reload button
            reload_button = QPushButton("↻")
            reload_button.setFixedSize(25, 25)
            reload_button.setStyleSheet(RELOAD_BUTTON_STYLE)
            label = QLabel()  # Create label here to reference it in lambda
            reload_button.clicked.connect(lambda: self.reload_message(box, label))
            
            button_layout.addWidget(stop_button)
            button_layout.addWidget(reload_button)
            header_layout.addWidget(button_container)

        header_layout.addStretch()
        box_layout.addLayout(header_layout)
        
        # Message content
        label = QLabel(message)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        box_layout.addWidget(label)
        
        if not is_user:
            box.original_prompt = self.current_prompt  # Store the prompt with the box
            
        return box, label if not is_user else None

    def reload_message(self, box, label):
        """Replace the specific AI response with a new one"""
        if not hasattr(box, 'original_prompt'):
            return
            
        self.is_generating = True
        self.should_stop = False
        self.disable_input()
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": self.model_selector.currentText(),
                    "prompt": box.original_prompt,
                    "system": self.SYSTEM_PROMPT,
                    "stream": True
                },
                stream=True
            )
            
            if response.status_code == 200:
                complete_response = []
                
                for line in response.iter_lines():
                    if self.should_stop:
                        response.close()
                        break
                        
                    if line:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            chunk = json_response['response']
                            complete_response.append(chunk)
                            
                            try:
                                markdown_text = ''.join(complete_response)
                                html_content = markdown2.markdown(
                                    markdown_text,
                                    extras=['fenced-code-blocks', 'code-friendly']
                                )
                                label.setText(f"<b>AI:</b> {html_content}")
                                QApplication.processEvents()
                                
                            except Exception as e:
                                print(f"Error formatting response: {str(e)}")
            else:
                label.setText("<b>AI:</b> Error: Failed to get response from Ollama")
        
        except requests.exceptions.RequestException as e:
            label.setText(f"<b>AI:</b> Error: Cannot connect to Ollama service: {str(e)}")
        
        self.is_generating = False
        self.should_stop = False
        self.enable_input()

    def send_message(self):
        user_message = self.input_field.text()
        if not user_message or self.is_generating:
            return
            
        self.current_prompt = user_message
        self.is_generating = True
        self.should_stop = False
        self.disable_input()
        
        # Store references to message boxes
        user_box, _ = self.create_message_box(True, user_message)
        self.current_user_box = user_box
        self.chat_layout.addWidget(user_box)
        
        ai_box, ai_label = self.create_message_box(False, "")
        self.current_ai_box = ai_box
        self.current_ai_label = ai_label
        self.chat_layout.addWidget(ai_box)
        
        # Scroll to bottom after adding new message
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().maximum()
            )
        
        # Enable stop button at the start of generation
        self.stop_button.setEnabled(True)
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": self.model_selector.currentText(),
                    "prompt": user_message,
                    "system": self.SYSTEM_PROMPT,
                    "stream": True
                },
                stream=True
            )
            
            if response.status_code == 200:
                complete_response = []
                
                for line in response.iter_lines():
                    if self.should_stop:
                        response.close()
                        break
                        
                    if line:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            chunk = json_response['response']
                            complete_response.append(chunk)
                            
                            try:
                                markdown_text = ''.join(complete_response)
                                html_content = markdown2.markdown(
                                    markdown_text,
                                    extras=['fenced-code-blocks', 'code-friendly']
                                )
                                ai_label.setText(f"<b>AI:</b> {html_content}")
                                QApplication.processEvents()
                                
                            except Exception as e:
                                print(f"Error formatting response: {str(e)}")
            else:
                ai_label.setText("<b>AI:</b> Error: Failed to get response from Ollama")
        
        except requests.exceptions.RequestException as e:
            ai_label.setText(f"<b>AI:</b> Error: Cannot connect to Ollama service: {str(e)}")
        
        self.is_generating = False
        self.should_stop = False
        self.stop_button.setEnabled(False)
        self.enable_input()
        self.input_field.clear()

    def clear_chat(self):
        """Clear all chat messages and reset references"""
        # First stop any ongoing generation
        if self.is_generating:
            self.should_stop = True
            self.stop_button.setEnabled(False)
            self.send_button.setEnabled(True)
            self.input_field.setEnabled(True)
            self.is_generating = False
            QApplication.processEvents()  # Process any pending events
        
        print(f"Items in chat layout before clearing: {self.chat_layout.count()}")
        
        # Remove ALL items from the layout, including the stretch
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add a new stretch at the end
        self.chat_layout.addStretch()
        
        # Force update the layout
        self.chat_layout.update()
        QApplication.processEvents()
        
        # Reset all references
        self.current_prompt = None
        self.current_user_box = None
        self.current_ai_box = None
        self.current_ai_label = None
        
        print(f"Items in chat layout after clearing: {self.chat_layout.count()}")

    def get_random_prompt(self):
        return random.choice(self.linux_prompts)

    def show_loading_overlay(self, show=True):
        if show:
            # Calculate size relative to chat display
            overlay_width = min(300, self.chat_display.width() - 40)
            overlay_height = min(200, self.chat_display.height() - 40)
            self.loading_overlay.resize(overlay_width, overlay_height)
            # Center in chat display
            x = (self.chat_display.width() - self.loading_overlay.width()) // 2
            y = (self.chat_display.height() - self.loading_overlay.height()) // 2
            self.loading_overlay.move(x, y)
            self.loading_overlay.show()
        else:
            self.loading_overlay.hide()

    def reload_model(self):
        current_model = self.model_selector.currentText()
        if not current_model:
            return
        
        # Cleanup any existing worker
        self.cleanup()
        
        # Show centered loading overlay and disable reload button
        self.show_loading_overlay(True)
        self.reload_button.setEnabled(False)
        
        # Create and start worker thread
        self.reload_worker = ReloadWorker(current_model)
        self.reload_worker.finished.connect(self.on_reload_finished)
        self.reload_worker.error.connect(self.on_reload_error)
        self.reload_worker.start()

    def closeEvent(self, event):
        """Handle application closing"""
        self.cleanup()
        super().closeEvent(event)

    def on_reload_finished(self):
        self.show_loading_overlay(False)
        self.reload_button.setEnabled(True)
        self.model_selector.setEnabled(True)

    def on_reload_error(self, error_message):
        self.display_system_message(f"Error: {error_message}")
        self.show_loading_overlay(False)
        self.reload_button.setEnabled(True)
        self.model_selector.setEnabled(True)

    def use_suggestion(self, suggestion):
        """Handle suggestion button clicks"""
        self.input_field.setText(suggestion)
        self.send_message()

    def refresh_suggestions(self):
        """Refresh the example questions in the existing suggestions box"""
        suggestions_box = [box for box in self.findChildren(QGroupBox) if isinstance(box, QGroupBox) and box.findChild(QLabel).text() == "Example Questions"]
        if suggestions_box:
            suggestions_box = suggestions_box[0]
            layout = suggestions_box.layout()
            
            # Skip the first widget (title widget) and remove the rest
            while layout.count() > 1:
                item = layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new random suggestion buttons
            for prompt in random.sample(self.linux_prompts, 3):
                suggestion_button = QPushButton(prompt)
                suggestion_button.clicked.connect(lambda checked, p=prompt: self.use_suggestion(p))
                layout.addWidget(suggestion_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

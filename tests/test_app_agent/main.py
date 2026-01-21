import sys, os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel

if 'QT_AGENT_PORT_FILE' in os.environ:
    from robotframework_qtexpert.agent import start_agent

class DemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgentDemoApp")
        self.setObjectName("mainWindow")
        layout = QVBoxLayout()
        self.line_edit = QLineEdit(self); self.line_edit.setObjectName("myInput")
        self.button = QPushButton("Click Me", self); self.button.setObjectName("myButton")
        self.button.clicked.connect(self.on_button_click)
        self.label = QLabel("", self); self.label.setObjectName("myLabel")
        layout.addWidget(self.line_edit); layout.addWidget(self.button); layout.addWidget(self.label)
        self.setLayout(layout)
    def on_button_click(self):
        self.label.setText(f"Hello, {self.line_edit.text()}!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoApp(); window.show()
    agent = None
    port_file_path = os.environ.get('QT_AGENT_PORT_FILE')
    if port_file_path:
        agent = start_agent(app)
        with open(port_file_path, 'w') as f: f.write(str(agent.port))
    sys.exit(app.exec())
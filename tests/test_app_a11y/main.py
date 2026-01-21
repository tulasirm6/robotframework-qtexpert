import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel

class DemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A11yDemoApp")
        layout = QVBoxLayout()
        self.line_edit = QLineEdit(self); self.line_edit.setObjectName("myInput")
        self.button = QPushButton("Click Me", self)
        self.button.clicked.connect(self.on_button_click)
        self.label = QLabel("", self)
        layout.addWidget(self.line_edit); layout.addWidget(self.button); layout.addWidget(self.label)
        self.setLayout(layout)
    def on_button_click(self):
        self.label.setText(f"Hello, {self.line_edit.text()}!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoApp(); window.show()
    sys.exit(app.exec())
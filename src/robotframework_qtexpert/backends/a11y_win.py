from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError
from .base import BaseBackend

class WinA11yBackend(BaseBackend):
    def __init__(self):
        self.app = None
        self.main_window = None

    def connect(self, app_path=None, window_title=None, timeout=30):
        if app_path: self.app = Application(backend="uia").start(app_path)
        else: self.app = Application(backend="uia").connect(title=window_title, timeout=timeout)
        self.main_window = self.app.window(title=window_title, timeout=timeout)
        self.main_window.wait('visible', timeout=timeout)

    def disconnect(self):
        self.main_window = None
        self.app = None

    def find_element(self, locator, locator_type='name'):
        try:
            return self.main_window.child_window(auto_id=locator)
        except ElementNotFoundError:
            return self.main_window.child_window(title=locator, control_type=locator_type)

    def click(self, element): element.click()
    def get_value(self, element): return element.get_value() if hasattr(element, 'get_value') else element.window_text()
    def set_value(self, element, value): element.set_edit_text(value)
    def close_app(self):
        if self.main_window: self.main_window.close()
        if self.app: self.app.kill()
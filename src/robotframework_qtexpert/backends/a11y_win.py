import importlib
from .base import BaseBackend

class WinA11yBackend(BaseBackend):
    def __init__(self):
        self.app = None
        self.main_window = None

    def _ensure_pywinauto(self):
        try:
            app_mod = importlib.import_module("pywinauto.application")
            find_mod = importlib.import_module("pywinauto.findwindows")
            return app_mod.Application, find_mod.ElementNotFoundError
        except (ImportError, ModuleNotFoundError):
            raise ImportError(
                "pywinauto is required for Windows Accessibility mode. "
                "Install it via 'pip install pywinauto'."
            )

    def connect(self, app_path=None, window_title=None, timeout=30):
        Application, _ = self._ensure_pywinauto()
        if app_path:
            self.app = Application(backend="uia").start(app_path)
        else:
            self.app = Application(backend="uia").connect(title=window_title, timeout=timeout)
        self.main_window = self.app.window(title=window_title, timeout=timeout)
        self.main_window.wait('visible', timeout=timeout)

    def disconnect(self):
        self.main_window = None
        self.app = None

    def find_element(self, locator, locator_type='name', **kwargs):
        _, ElementNotFoundError = self._ensure_pywinauto()
        try:
            return self.main_window.child_window(auto_id=locator)
        except ElementNotFoundError:
            return self.main_window.child_window(title=locator, control_type=locator_type)

    def click(self, element, *args, **kwargs):
        element.click()

    def get_value(self, element):
        return element.get_value() if hasattr(element, 'get_value') else element.window_text()

    def set_value(self, element, value):
        element.set_edit_text(value)

    def close_app(self):
        if self.main_window:
            try:
                self.main_window.close()
            except Exception:
                pass
        if self.app:
            try:
                self.app.kill()
            except Exception:
                pass
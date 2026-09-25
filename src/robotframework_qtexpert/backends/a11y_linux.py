import time
import os
from .base import BaseBackend
from ..locators import parse_locator

class LinuxA11yBackend(BaseBackend):
    def __init__(self):
        self._pyatspi = None
        self.desktop = None
        self.app = None

    def _ensure_pyatspi(self):
        if self._pyatspi is None:
            try:
                import importlib
                self._pyatspi = importlib.import_module("pyatspi")
                self.desktop = self._pyatspi.Registry.getDesktop(0)
            except (ImportError, ModuleNotFoundError):
                raise ImportError(
                    "pyatspi is required for Linux Accessibility mode. "
                    "On Linux, install it via system packages (e.g. 'sudo apt-get install python3-pyatspi')."
                )

    def connect(self, app_path=None, window_title=None, timeout=30):
        self._ensure_pyatspi()
        deadline = time.time() + float(timeout)
        expected_title = window_title.strip() if window_title else None
        app_base = os.path.basename(app_path) if app_path else None

        while time.time() < deadline:
            for app in self.desktop:
                # 1. Match by app.name directly
                if expected_title and app.name == expected_title:
                    self.app = app
                    return
                if app_base and (app.name == app_base or app_base in app.name):
                    self.app = app
                    return

                # 2. Match by child window title (ROLE_FRAME / ROLE_WINDOW)
                if expected_title:
                    try:
                        for child in app:
                            if child.name == expected_title:
                                self.app = child
                                return
                    except Exception:
                        pass
            time.sleep(0.5)

        raise ConnectionError(
            f"Application '{window_title or app_path}' not found in AT-SPI desktop within {timeout}s. "
            "Ensure QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 and qt-at-spi are active."
        )

    def disconnect(self):
        self.app = None

    def _find_element_recursive(self, acc, criteria):
        if not acc:
            return None

        # Check criteria against current element
        matches = True
        if 'objectName' in criteria or 'name' in criteria:
            target_name = criteria.get('objectName') or criteria.get('name')
            if acc.name != target_name and acc.description != target_name:
                matches = False

        if 'text' in criteria:
            target_text = criteria['text']
            actual_text = self.get_value(acc)
            if actual_text != target_text:
                matches = False

        if matches and ('objectName' in criteria or 'name' in criteria or 'text' in criteria):
            return acc

        for child in acc:
            found = self._find_element_recursive(child, criteria)
            if found:
                return found
        return None

    def find_element(self, locator, **kwargs):
        criteria = parse_locator(locator)
        element = self._find_element_recursive(self.app, criteria)
        if not element:
            raise ValueError(f"Accessibility element matching '{locator}' not found.")
        return element

    def click(self, element, **kwargs):
        action = None
        for i in range(element.get_nActions()):
            act_name = element.getActionName(i).lower()
            if act_name in ('click', 'press', 'activate'):
                action = i
                break
        if action is not None:
            element.doAction(action)
        elif element.get_nActions() > 0:
            element.doAction(0)

    def get_value(self, element):
        try:
            if element.getRole() == self._pyatspi.ROLE_TEXT:
                return element.queryText().getText(0, -1)
        except Exception:
            pass
        return element.name or element.description or ""

    def set_value(self, element, value):
        try:
            element.queryEditableText().setTextContents(str(value))
        except Exception:
            raise TypeError("Cannot set value on non-editable text element via AT-SPI.")

    def close_app(self):
        if self.app:
            try:
                self.app.queryApplication().close()
            except Exception:
                pass
            self.disconnect()
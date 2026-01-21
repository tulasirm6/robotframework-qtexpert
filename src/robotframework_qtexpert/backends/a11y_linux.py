import pyatspi
from .base import BaseBackend

class LinuxA11yBackend(BaseBackend):
    def __init__(self):
        self.desktop = pyatspi.Registry.getDesktop(0)
        self.app = None

    def connect(self, app_path=None, window_title=None, timeout=30):
        for app in self.desktop:
            if app.name == window_title:
                self.app = app
                return
        raise ConnectionError(f"Application '{window_title}' not found.")

    def disconnect(self): self.app = None

    def _find_element_recursive(self, acc, locator):
        if acc.name == locator: return acc
        for child in acc:
            found = self._find_element_recursive(child, locator)
            if found: return found
        return None

    def find_element(self, locator, **kwargs):
        element = self._find_element_recursive(self.app, locator)
        if not element: raise ValueError(f"Element '{locator}' not found.")
        return element

    def click(self, element):
        action = None
        for i in range(element.get_nActions()):
            if element.getActionName(i) == 'click': action = i; break
        if action is not None: element.doAction(action)

    def get_value(self, element):
        if element.getRole() == pyatspi.ROLE_TEXT:
            return element.queryText().getText(0, -1)
        return element.name

    def set_value(self, element, value):
        if element.getRole() == pyatspi.ROLE_TEXT:
            element.queryEditableText().setTextContents(value)
        else:
            raise TypeError("Cannot set value on non-text element.")

    def close_app(self):
        if self.app:
            self.app.queryApplication().close()
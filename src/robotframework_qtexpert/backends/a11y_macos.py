from Cocoa import NSWorkspace
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionOnScreenOnly
from PyObjCTools import AppHelper
from .base import BaseBackend

class MacA11yBackend(BaseBackend):
    def __init__(self):
        self.app_ref = None
        self.window_element = None

    def connect(self, app_path=None, window_title=None, timeout=30):
        app_name = os.path.basename(app_path).split('.')[0] if app_path else None
        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if (app_name and app.bundleIdentifier().endswith(app_name)) or (window_title and app.localizedName() == window_title):
                self.app_ref = app
                self.window_element = self._get_window_element(app.processIdentifier(), window_title)
                if not self.window_element: raise ConnectionError(f"Window '{window_title}' not found for app.")
                return
        raise ConnectionError(f"Application '{app_name or window_title}' not found.")

    def _get_window_element(self, pid, window_title):
        from Quartz import AXUIElementCreateApplication, AXUIElementCopyAttributeValue, kAXWindowsAttribute, kAXTitleAttribute, kAXErrorSuccess
        app_ref = AXUIElementCreateApplication(pid)
        result, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)
        if result != kAXErrorSuccess: return None
        for window in windows:
            result, title = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
            if result == kAXErrorSuccess and title == window_title:
                return window
        return None

    def disconnect(self):
        self.app_ref = None
        self.window_element = None

    def _find_element_recursive(self, element, locator):
        from Quartz import (AXUIElementCopyAttributeValue, kAXChildrenAttribute, kAXErrorSuccess, kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute)
        result, title = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
        if result == kAXErrorSuccess and title == locator: return element
        result, children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
        if result == kAXErrorSuccess:
            for child in children:
                found = self._find_element_recursive(child, locator)
                if found: return found
        return None

    def find_element(self, locator, **kwargs):
        element = self._find_element_recursive(self.window_element, locator)
        if not element: raise ValueError(f"Element '{locator}' not found.")
        return element

    def click(self, element):
        from Quartz import AXUIElementPerformAction, kAXPressAction, kAXErrorSuccess
        result = AXUIElementPerformAction(element, kAXPressAction)
        if result != kAXErrorSuccess: raise RuntimeError("Failed to click element.")

    def get_value(self, element):
        from Quartz import AXUIElementCopyAttributeValue, kAXValueAttribute, kAXTitleAttribute, kAXErrorSuccess
        result, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
        if result == kAXErrorSuccess: return str(value)
        result, title = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
        if result == kAXErrorSuccess: return str(title)
        return ""

    def set_value(self, element, value):
        from Quartz import AXUIElementSetAttributeValue, kAXValueAttribute, kAXErrorSuccess
        result = AXUIElementSetAttributeValue(element, kAXValueAttribute, value)
        if result != kAXErrorSuccess: raise RuntimeError("Failed to set value.")

    def close_app(self):
        if self.app_ref: self.app_ref.terminate()
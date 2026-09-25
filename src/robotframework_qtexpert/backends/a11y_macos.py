import os
import sys
import importlib
from .base import BaseBackend

class MacA11yBackend(BaseBackend):
    def __init__(self):
        self.app_ref = None
        self.window_element = None

    def _ensure_pyobjc(self):
        try:
            cocoa = importlib.import_module("Cocoa")
            quartz = importlib.import_module("Quartz")
            return cocoa, quartz
        except (ImportError, ModuleNotFoundError):
            raise ImportError(
                "pyobjc-framework-Cocoa and pyobjc-framework-Quartz are required for macOS Accessibility mode. "
                "Install them via 'pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz'."
            )

    def connect(self, app_path=None, window_title=None, timeout=30):
        cocoa, _ = self._ensure_pyobjc()
        app_name = os.path.basename(app_path).split('.')[0] if app_path else None
        running_apps = cocoa.NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if (app_name and app.bundleIdentifier() and app.bundleIdentifier().endswith(app_name)) or (window_title and app.localizedName() == window_title):
                self.app_ref = app
                self.window_element = self._get_window_element(app.processIdentifier(), window_title)
                if not self.window_element:
                    raise ConnectionError(f"Window '{window_title}' not found for app.")
                return
        raise ConnectionError(f"Application '{app_name or window_title}' not found.")

    def _get_window_element(self, pid, window_title):
        _, quartz = self._ensure_pyobjc()
        app_ref = quartz.AXUIElementCreateApplication(pid)
        result, windows = quartz.AXUIElementCopyAttributeValue(app_ref, quartz.kAXWindowsAttribute, None)
        if result != quartz.kAXErrorSuccess or not windows:
            return None
        for window in windows:
            result, title = quartz.AXUIElementCopyAttributeValue(window, quartz.kAXTitleAttribute, None)
            if result == quartz.kAXErrorSuccess and title == window_title:
                return window
        return None

    def disconnect(self):
        self.app_ref = None
        self.window_element = None

    def _find_element_recursive(self, element, locator):
        _, quartz = self._ensure_pyobjc()
        result, title = quartz.AXUIElementCopyAttributeValue(element, quartz.kAXTitleAttribute, None)
        if result == quartz.kAXErrorSuccess and title == locator:
            return element
        result, children = quartz.AXUIElementCopyAttributeValue(element, quartz.kAXChildrenAttribute, None)
        if result == quartz.kAXErrorSuccess and children:
            for child in children:
                found = self._find_element_recursive(child, locator)
                if found:
                    return found
        return None

    def find_element(self, locator, **kwargs):
        element = self._find_element_recursive(self.window_element, locator)
        if not element:
            raise ValueError(f"Element '{locator}' not found.")
        return element

    def click(self, element, *args, **kwargs):
        _, quartz = self._ensure_pyobjc()
        result = quartz.AXUIElementPerformAction(element, quartz.kAXPressAction)
        if result != quartz.kAXErrorSuccess:
            raise RuntimeError("Failed to click element.")

    def get_value(self, element):
        _, quartz = self._ensure_pyobjc()
        result, value = quartz.AXUIElementCopyAttributeValue(element, quartz.kAXValueAttribute, None)
        if result == quartz.kAXErrorSuccess and value is not None:
            return str(value)
        result, title = quartz.AXUIElementCopyAttributeValue(element, quartz.kAXTitleAttribute, None)
        if result == quartz.kAXErrorSuccess and title is not None:
            return str(title)
        return ""

    def set_value(self, element, value):
        _, quartz = self._ensure_pyobjc()
        result = quartz.AXUIElementSetAttributeValue(element, quartz.kAXValueAttribute, value)
        if result != quartz.kAXErrorSuccess:
            raise RuntimeError("Failed to set value.")

    def close_app(self):
        if self.app_ref:
            try:
                self.app_ref.terminate()
            except Exception:
                pass
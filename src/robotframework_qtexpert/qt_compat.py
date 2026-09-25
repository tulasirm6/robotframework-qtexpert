# src/robotframework_qtexpert/qt_compat.py
"""
Qt Compatibility layer supporting PyQt5, PySide2, PyQt6, and PySide6.
Inspects active modules first to prevent fatal Qt5/Qt6 C++ ABI collisions,
respects the QT_API environment variable, and uses dynamic imports to avoid
static IDE import resolution errors.
"""
import os
import sys
import importlib

_QtCore = None
_QtWidgets = None
_QtGui = None
_QtTest = None
QT_BINDING = None
Signal = None
Slot = None

def _try_import(binding_name):
    global _QtCore, _QtWidgets, _QtGui, _QtTest, QT_BINDING, Signal, Slot
    try:
        QtCore = importlib.import_module(f"{binding_name}.QtCore")
        QtWidgets = importlib.import_module(f"{binding_name}.QtWidgets")
        QtGui = importlib.import_module(f"{binding_name}.QtGui")
        QtTest = importlib.import_module(f"{binding_name}.QtTest")

        Signal = getattr(QtCore, 'pyqtSignal', getattr(QtCore, 'Signal', None))
        Slot = getattr(QtCore, 'pyqtSlot', getattr(QtCore, 'Slot', None))

        _QtCore = QtCore
        _QtWidgets = QtWidgets
        _QtGui = QtGui
        _QtTest = QtTest
        QT_BINDING = binding_name
        return True
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False

def _import_qt():
    global _QtCore, _QtWidgets, _QtGui, _QtTest, QT_BINDING

    if _QtCore is not None:
        return

    # 1. Respect explicit QT_API / QT_BINDING environment variable
    preferred = os.environ.get('QT_API', os.environ.get('QT_BINDING', '')).strip().lower()
    mapping = {
        'pyqt5': 'PyQt5',
        'pyside2': 'PySide2',
        'pyqt6': 'PyQt6',
        'pyside6': 'PySide6',
    }
    if preferred in mapping:
        if _try_import(mapping[preferred]):
            return

    # 2. Check if a Qt binding is already loaded in sys.modules
    for mod_key, binding_name in [
        ('PyQt5.QtCore', 'PyQt5'),
        ('PyQt5', 'PyQt5'),
        ('PySide2.QtCore', 'PySide2'),
        ('PySide2', 'PySide2'),
        ('PyQt6.QtCore', 'PyQt6'),
        ('PyQt6', 'PyQt6'),
        ('PySide6.QtCore', 'PySide6'),
        ('PySide6', 'PySide6'),
    ]:
        if mod_key in sys.modules:
            if _try_import(binding_name):
                return

    # 3. Default search order: try PyQt5/PySide2 first if requested or general fallback
    order = ['PyQt5', 'PySide2', 'PyQt6', 'PySide6']
    for candidate in order:
        if _try_import(candidate):
            return

    # Also try Qt6 if Qt5 wasn't installed
    alt_order = ['PyQt6', 'PySide6']
    for candidate in alt_order:
        if _try_import(candidate):
            return

# Initialize bindings if available
try:
    _import_qt()
except Exception:
    pass

QtCore = _QtCore
QtWidgets = _QtWidgets
QtGui = _QtGui
QtTest = _QtTest
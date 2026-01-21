# src/robotframework_qtexpert/qt_compat.py
import sys

# This will hold our imported Qt modules
_QtCore = None
_QtWidgets = None
_QtTest = None
QT_BINDING = None

def _import_qt():
    """
    Imports the first available Qt binding.
    Tries in order: PyQt6, PySide6, PyQt5, PySide2.
    """
    global _QtCore, _QtWidgets, _QtTest, QT_BINDING

    if _QtCore is not None:
        return # Already imported

    try:
        from PyQt6 import QtCore, QtWidgets, QtTest
        QT_BINDING = 'PyQt6'
    except ImportError:
        try:
            from PySide6 import QtCore, QtWidgets, QtTest
            QT_BINDING = 'PySide6'
        except ImportError:
            try:
                from PyQt5 import QtCore, QtWidgets, QtTest
                QT_BINDING = 'PyQt5'
            except ImportError:
                try:
                    from PySide2 import QtCore, QtWidgets, QtTest
                    QT_BINDING = 'PySide2'
                except ImportError:
                    raise ImportError(
                        "No Qt binding found. Please install one of: PyQt6, PySide6, PyQt5, or PySide2. "
                        "e.g., pip install PyQt6"
                    )
    
    _QtCore = QtCore
    _QtWidgets = QtWidgets
    _QtTest = QtTest

# Call the import function when the module is loaded
_import_qt()

# Expose the modules to the rest of our library
QtCore = _QtCore
QtWidgets = _QtWidgets
QtTest = _QtTest
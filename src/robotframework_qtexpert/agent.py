# src/robotframework_qtexpert/agent.py
"""
Qt In-Process Test Agent with 100% Thread-Safe Main GUI Thread Dispatching.
Compatible with PyQt5, PySide2, PyQt6, and PySide6 on Linux, Windows, and macOS.
"""
import sys
import os
import xmlrpc.server
from threading import Thread, Event
from queue import Queue

from .qt_compat import QtCore, QtWidgets, QtTest, Signal, Slot, QT_BINDING
from .locators import parse_locator

_BaseQObject = getattr(QtCore, 'QObject', object) if QtCore else object

class _MainThreadDispatcher(_BaseQObject):
    """
    QObject residing in the Qt main GUI thread.
    Executes functions requested by background worker threads using BlockingQueuedConnection.
    """
    if Signal is not None and QtCore is not None:
        _exec_signal = Signal(object, object, object, object)
    else:
        _exec_signal = None

    def __init__(self, parent=None):
        if QtCore and issubclass(_BaseQObject, QtCore.QObject):
            super().__init__(parent)
        else:
            super().__init__()
        self._queue = Queue()
        if self._exec_signal and QtCore:
            conn_type = getattr(getattr(QtCore.Qt, 'ConnectionType', QtCore.Qt), 'BlockingQueuedConnection', None)
            if conn_type is None:
                conn_type = getattr(QtCore.Qt, 'BlockingQueuedConnection', None)
            self._exec_signal.connect(self._handle_signal, conn_type)

    def _handle_signal(self, func, args, kwargs, result_holder):
        try:
            result_holder['result'] = func(*args, **kwargs)
            result_holder['success'] = True
        except Exception as e:
            result_holder['error'] = str(e)
            result_holder['success'] = False

    def dispatch(self, func, *args, **kwargs):
        """Dispatches func to Qt main GUI thread safely."""
        app = QtWidgets.QApplication.instance() if QtWidgets else None
        if not app:
            return func(*args, **kwargs)

        # If already on the Qt main GUI thread, execute directly
        if QtCore.QThread.currentThread() == app.thread():
            return func(*args, **kwargs)

        result_holder = {}
        if self._exec_signal:
            self._exec_signal.emit(func, args, kwargs, result_holder)
            if not result_holder.get('success', False):
                raise RuntimeError(result_holder.get('error', 'Main thread dispatch failed'))
            return result_holder.get('result')

        # Fallback using QTimer and threading.Event
        event = Event()
        def runner():
            try:
                result_holder['result'] = func(*args, **kwargs)
                result_holder['success'] = True
            except Exception as e:
                result_holder['error'] = str(e)
                result_holder['success'] = False
            finally:
                event.set()

        QtCore.QTimer.singleShot(0, runner)
        event.wait(timeout=15.0)
        if not result_holder.get('success', False):
            raise RuntimeError(result_holder.get('error', 'Main thread dispatch timed out'))
        return result_holder.get('result')


class QtAgent:
    """
    The XML-RPC server running inside the AUT.
    All operations touching QWidgets are safely marshaled onto the Qt main GUI thread.
    """
    def __init__(self, app_instance, port=0):
        self._app = app_instance
        self._dispatcher = _MainThreadDispatcher(parent=app_instance)
        
        # Start XML-RPC server on localhost
        self._server = xmlrpc.server.SimpleXMLRPCServer(
            ('127.0.0.1', port), logRequests=False, allow_none=True
        )
        self.port = self._server.server_address[1]
        
        # Register exposed methods
        self._server.register_function(self.ping)
        self._server.register_function(self.find_widget)
        self._server.register_function(self.get_property)
        self._server.register_function(self.set_property)
        self._server.register_function(self.click)
        self._server.register_function(self.key_clicks)
        self._server.register_function(self.press_key)
        self._server.register_function(self.clear_text)
        self._server.register_function(self.select_tab)
        self._server.register_function(self.select_combo_item)
        self._server.register_function(self.dump_tree)
        self._server.register_function(self.close_app)
        
        # Run server in daemon worker thread
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"[QtAgent] QtAgent ({QT_BINDING}) listening on port {self.port}")

    def ping(self):
        return True

    # -------------------------------------------------------------
    # Internal Main-Thread Implementations
    # -------------------------------------------------------------
    def _matches_criteria(self, w, criteria):
        if not w:
            return False
        
        if 'objectName' in criteria:
            if w.objectName() != criteria['objectName']:
                return False

        if 'className' in criteria:
            expected_class = criteria['className']
            meta_name = w.metaObject().className()
            if meta_name != expected_class and not w.inherits(expected_class):
                return False

        if 'text' in criteria:
            expected_text = criteria['text']
            actual_text = ""
            if hasattr(w, 'text') and callable(w.text):
                actual_text = str(w.text())
            elif hasattr(w, 'title') and callable(w.title):
                actual_text = str(w.title())
            elif hasattr(w, 'windowTitle') and callable(w.windowTitle):
                actual_text = str(w.windowTitle())
            if actual_text != expected_text:
                return False

        if 'windowTitle' in criteria:
            win = w.window()
            if not win or win.windowTitle() != criteria['windowTitle']:
                return False

        if 'visible' in criteria:
            if bool(w.isVisible()) != bool(criteria['visible']):
                return False

        if 'enabled' in criteria:
            if bool(w.isEnabled()) != bool(criteria['enabled']):
                return False

        return True

    def _activate_tab_for_widget(self, w):
        if not w:
            return
        app = QtWidgets.QApplication.instance()
        curr = w
        while curr:
            parent = curr.parent() if hasattr(curr, 'parent') else None
            if parent:
                anc = parent
                while anc:
                    is_tab = (hasattr(anc, 'metaObject') and anc.metaObject().className() == 'QTabWidget') or \
                             (hasattr(anc, 'inherits') and anc.inherits('QTabWidget'))
                    if is_tab and hasattr(anc, 'indexOf') and hasattr(anc, 'setCurrentIndex'):
                        try:
                            idx = anc.indexOf(curr)
                            if idx >= 0 and anc.currentIndex() != idx:
                                anc.setCurrentIndex(idx)
                                if app and hasattr(app, 'processEvents'):
                                    app.processEvents()
                        except Exception:
                            pass
                        break
                    anc = anc.parent() if hasattr(anc, 'parent') else None
            curr = parent

    def _resolve_widget(self, locator, auto_activate_tab=False):
        criteria = parse_locator(locator)
        app = QtWidgets.QApplication.instance()
        if not app:
            return None

        found = None
        # Search all active widgets
        widgets = app.allWidgets()
        for w in widgets:
            if self._matches_criteria(w, criteria):
                found = w
                break

        # Also check top-level windows specifically
        if not found:
            for w in app.topLevelWidgets():
                if self._matches_criteria(w, criteria):
                    found = w
                    break

        if found and auto_activate_tab:
            self._activate_tab_for_widget(found)

        return found

    def _dump_widget(self, w):
        if not w:
            return {}
        info = {
            "className": w.metaObject().className(),
            "objectName": w.objectName(),
            "visible": bool(w.isVisible()),
            "enabled": bool(w.isEnabled()),
        }
        if hasattr(w, 'text') and callable(w.text):
            info["text"] = str(w.text())
        elif hasattr(w, 'windowTitle') and callable(w.windowTitle) and w.windowTitle():
            info["windowTitle"] = str(w.windowTitle())

        children = []
        for child in w.findChildren(QtWidgets.QWidget):
            if child.parent() == w:
                children.append(self._dump_widget(child))
        if children:
            info["children"] = children
        return info

    # -------------------------------------------------------------
    # Dispatched Public API
    # -------------------------------------------------------------
    def find_widget(self, locator):
        def _task():
            w = self._resolve_widget(locator)
            return w is not None
        return self._dispatcher.dispatch(_task)

    def get_property(self, locator, property_name):
        def _task():
            w = self._resolve_widget(locator)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            if property_name in ('text', 'plainText'):
                if hasattr(w, 'toPlainText'):
                    return str(w.toPlainText())
            val = w.property(property_name)
            if val is not None:
                return str(val)
            attr = getattr(w, property_name, None)
            if callable(attr):
                return str(attr())
            return str(attr) if attr is not None else ""
        return self._dispatcher.dispatch(_task)

    def set_property(self, locator, property_name, value):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            if property_name == 'text':
                if hasattr(w, 'setText'):
                    w.setText(str(value))
                    return True
                elif hasattr(w, 'setPlainText'):
                    w.setPlainText(str(value))
                    return True
            w.setProperty(property_name, value)
            return True
        return self._dispatcher.dispatch(_task)

    def click(self, locator, button="left", x=-1, y=-1, double=False):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            
            btn_name = button.lower()
            btn_enum = getattr(QtCore.Qt, 'MouseButton', QtCore.Qt)
            if btn_name == 'right':
                qt_btn = getattr(btn_enum, 'RightButton', getattr(QtCore.Qt, 'RightButton', None))
            elif btn_name == 'middle':
                qt_btn = getattr(btn_enum, 'MiddleButton', getattr(QtCore.Qt, 'MiddleButton', getattr(QtCore.Qt, 'MidButton', None)))
            else:
                qt_btn = getattr(btn_enum, 'LeftButton', getattr(QtCore.Qt, 'LeftButton', None))

            if x >= 0 and y >= 0:
                pos = QtCore.QPoint(x, y)
            elif hasattr(QtWidgets, 'QCheckBox') and isinstance(w, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)):
                pos = QtCore.QPoint(10, max(w.height() // 2, 5))
            else:
                pos = QtCore.QPoint(w.width() // 2, w.height() // 2)
            no_mod = getattr(getattr(QtCore.Qt, 'KeyboardModifier', QtCore.Qt), 'NoModifier', getattr(QtCore.Qt, 'NoModifier', None))

            if QtTest and hasattr(QtTest, 'QTest'):
                if double:
                    QtTest.QTest.mouseDClick(w, qt_btn, no_mod, pos)
                else:
                    QtTest.QTest.mouseClick(w, qt_btn, no_mod, pos)
            else:
                if hasattr(w, 'click'):
                    w.click()
                elif hasattr(w, 'trigger'):
                    w.trigger()
                else:
                    w.setFocus()

            if hasattr(w, 'linkActivated') and hasattr(w, 'text'):
                txt = w.text() if callable(w.text) else str(getattr(w, 'text', ''))
                import re
                m = re.search(r'href=[\'"]([^\'"]+)[\'"]', txt)
                if m:
                    try:
                        w.linkActivated.emit(m.group(1))
                    except Exception:
                        pass
            return True
        return self._dispatcher.dispatch(_task)

    def key_clicks(self, locator, text, delay_ms=-1):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            w.setFocus()
            no_mod = getattr(getattr(QtCore.Qt, 'KeyboardModifier', QtCore.Qt), 'NoModifier', getattr(QtCore.Qt, 'NoModifier', None))
            if QtTest and hasattr(QtTest, 'QTest'):
                QtTest.QTest.keyClicks(w, text, no_mod, delay_ms if delay_ms >= 0 else 0)
            else:
                if hasattr(w, 'setText'):
                    w.setText(text)
                elif hasattr(w, 'setPlainText'):
                    w.setPlainText(text)
            return True
        return self._dispatcher.dispatch(_task)

    def press_key(self, locator, key_name, modifiers=""):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            w.setFocus()
            mod_enum = getattr(QtCore.Qt, 'KeyboardModifier', QtCore.Qt)
            no_mod = getattr(mod_enum, 'NoModifier', getattr(QtCore.Qt, 'NoModifier', None))
            mod = no_mod
            if "ctrl" in modifiers.lower():
                mod = mod | getattr(mod_enum, 'ControlModifier', getattr(QtCore.Qt, 'ControlModifier', 0))
            if "shift" in modifiers.lower():
                mod = mod | getattr(mod_enum, 'ShiftModifier', getattr(QtCore.Qt, 'ShiftModifier', 0))
            if "alt" in modifiers.lower():
                mod = mod | getattr(mod_enum, 'AltModifier', getattr(QtCore.Qt, 'AltModifier', 0))

            key_code = getattr(QtCore.Qt, f"Key_{key_name}", None)
            if key_code and QtTest and hasattr(QtTest, 'QTest'):
                QtTest.QTest.keyClick(w, key_code, mod)
                return True
            return False
        return self._dispatcher.dispatch(_task)

    def clear_text(self, locator):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            if hasattr(w, 'clear'):
                w.clear()
            elif hasattr(w, 'setText'):
                w.setText("")
            elif hasattr(w, 'setPlainText'):
                w.setPlainText("")
            else:
                w.setProperty('text', "")
            return True
        return self._dispatcher.dispatch(_task)

    def select_tab(self, locator, tab):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=False)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            is_tab = (hasattr(w, 'metaObject') and w.metaObject().className() == 'QTabWidget') or \
                     (hasattr(w, 'inherits') and w.inherits('QTabWidget'))
            if not is_tab:
                raise ValueError(f"Widget '{locator}' is not a QTabWidget.")

            app = QtWidgets.QApplication.instance()
            if isinstance(tab, int) or (isinstance(tab, str) and tab.isdigit()):
                idx = int(tab)
                if 0 <= idx < w.count():
                    w.setCurrentIndex(idx)
                    if app and hasattr(app, 'processEvents'):
                        app.processEvents()
                    return True
                raise ValueError(f"Tab index {idx} out of range (0..{w.count()-1})")

            target_str = str(tab).strip().lower()
            for i in range(w.count()):
                tab_text = w.tabText(i).strip().lower()
                if tab_text == target_str or target_str in tab_text:
                    w.setCurrentIndex(i)
                    if app and hasattr(app, 'processEvents'):
                        app.processEvents()
                    return True
            raise ValueError(f"Tab '{tab}' not found in QTabWidget '{locator}'. Available tabs: {[w.tabText(i) for i in range(w.count())]}")
        return self._dispatcher.dispatch(_task)

    def select_combo_item(self, locator, item):
        def _task():
            w = self._resolve_widget(locator, auto_activate_tab=True)
            if not w:
                raise ValueError(f"Widget '{locator}' not found.")
            is_combo = (hasattr(w, 'metaObject') and w.metaObject().className() == 'QComboBox') or \
                       (hasattr(w, 'inherits') and w.inherits('QComboBox'))
            if not is_combo:
                raise ValueError(f"Widget '{locator}' is not a QComboBox.")

            app = QtWidgets.QApplication.instance()
            if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
                idx = int(item)
                if 0 <= idx < w.count():
                    w.setCurrentIndex(idx)
                    if app and hasattr(app, 'processEvents'):
                        app.processEvents()
                    return True
                raise ValueError(f"Combo index {idx} out of range (0..{w.count()-1})")

            target_str = str(item).strip().lower()
            for i in range(w.count()):
                text = w.itemText(i).strip().lower()
                if text == target_str or target_str in text:
                    w.setCurrentIndex(i)
                    if app and hasattr(app, 'processEvents'):
                        app.processEvents()
                    return True
            raise ValueError(f"Option '{item}' not found in QComboBox '{locator}'. Available: {[w.itemText(i) for i in range(w.count())]}")
        return self._dispatcher.dispatch(_task)

    def dump_tree(self, locator=None):
        def _task():
            app = QtWidgets.QApplication.instance()
            if not app:
                return {}
            if locator:
                w = self._resolve_widget(locator)
                return self._dump_widget(w) if w else {}
            roots = []
            for w in app.topLevelWidgets():
                if w.isVisible():
                    roots.append(self._dump_widget(w))
            return {"screens": roots}
        return self._dispatcher.dispatch(_task)

    def close_app(self):
        def _task():
            self._app.quit()
            return True
        return self._dispatcher.dispatch(_task)


def start_agent(app_instance, port=0):
    """Convenience function to start the agent safely."""
    return QtAgent(app_instance, port=port)
# src/robotframework_qtexpert/agent.py
import sys
import xmlrpc.server
from threading import Thread

# This agent must be able to run with any Qt binding.
# We use the same compatibility logic as the library.
from .qt_compat import QtCore, QtWidgets, QT_BINDING

class QtAgent:
    """
    The XML-RPC server that runs inside the AUT.
    It exposes methods to control the Qt application.
    """
    def __init__(self, app_instance):
        self._app = app_instance
        # Find a free port
        self._server = xmlrpc.server.SimpleXMLRPCServer(
            ('localhost', 0), logRequests=False, allow_none=True
        )
        self.port = self._server.server_address[1]
        
        # Register methods to be exposed to the client
        self._server.register_function(self.find_widget)
        self._server.register_function(self.get_property)
        self._server.register_function(self.set_property)
        self._server.register_function(self.click)
        self._server.register_function(self.close_app)
        
        # Run the server in a separate thread so it doesn't block the Qt event loop
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"QtAgent for {QT_BINDING} started on port {self.port}")

    def find_widget(self, name, widget_type_name=None):
        """Finds a widget by its object name."""
        widget_type = getattr(QtWidgets, widget_type_name, QtWidgets.QWidget) if widget_type_name else QtWidgets.QWidget
        for widget in self._app.topLevelWidgets():
            found = widget.findChild(widget_type, name)
            if found:
                return True # Return True for success
        return False # Return False for failure

    def get_property(self, name, property_name, widget_type_name=None):
        """Gets a property of a widget."""
        widget_type = getattr(QtWidgets, widget_type_name, QtWidgets.QWidget) if widget_type_name else QtWidgets.QWidget
        for widget in self._app.topLevelWidgets():
            found = widget.findChild(widget_type, name)
            if found:
                return str(getattr(found, property_name, None))
        return None

    def set_property(self, name, property_name, value, widget_type_name=None):
        """Sets a property of a widget."""
        widget_type = getattr(QtWidgets, widget_type_name, QtWidgets.QWidget) if widget_type_name else QtWidgets.QWidget
        for widget in self._app.topLevelWidgets():
            found = widget.findChild(widget_type, name)
            if found:
                setattr(found, property_name, value)
                return True
        return False

    def click(self, name, widget_type_name=None):
        """Simulates a click on a widget."""
        widget_type = getattr(QtWidgets, widget_type_name, QtWidgets.QWidget) if widget_type_name else QtWidgets.QWidget
        for widget in self._app.topLevelWidgets():
            found = widget.findChild(widget_type, name)
            if found:
                found.click()
                return True
        return False
        
    def close_app(self):
        """Closes the application."""
        self._app.quit()
        return True

def start_agent(app_instance):
    """Convenience function to start the agent."""
    return QtAgent(app_instance)
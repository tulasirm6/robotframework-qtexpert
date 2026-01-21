import os
import xmlrpc.client
from .base import BaseBackend

class AgentBackend(BaseBackend):
    def __init__(self):
        self._rpc_client = None

    def connect(self, port_file_path=None, port=None):
        if not port_file_path and not port:
            raise ValueError("Provide 'port_file_path' or 'port'.")
        if port_file_path:
            with open(port_file_path, 'r') as f: port = int(f.read().strip())
            os.remove(port_file_path)
        self._rpc_client = xmlrpc.client.ServerProxy(f"http://localhost:{port}", allow_none=True)
        self._rpc_client.system.listMethods()

    def disconnect(self): self._rpc_client = None

    def find_element(self, locator, widget_type_name=None):
        if not self._rpc_client.find_widget(locator, widget_type_name):
            raise ValueError(f"Element '{locator}' not found.")
        return locator

    def click(self, element): self._rpc_client.click(element)
    def get_value(self, element): return self._rpc_client.get_property(element, 'text')
    def set_value(self, element, value): self._rpc_client.set_property(element, 'text', value)
    def close_app(self): self._rpc_client.close_app()
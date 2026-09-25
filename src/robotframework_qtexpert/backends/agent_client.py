import os
import time
import xmlrpc.client
from .base import BaseBackend

class AgentBackend(BaseBackend):
    def __init__(self):
        self._rpc_client = None

    def connect(self, port_file_path=None, port=None, timeout=15.0):
        if not port_file_path and not port:
            raise ValueError("Provide 'port_file_path' or 'port'.")

        deadline = time.time() + float(timeout)
        if port_file_path:
            # Poll until port file exists and is populated
            port_val = None
            last_err = None
            while time.time() < deadline:
                if os.path.exists(port_file_path):
                    try:
                        with open(port_file_path, 'r') as f:
                            content = f.read().strip()
                        if content:
                            port_val = int(content)
                            break
                    except Exception as e:
                        last_err = e
                time.sleep(0.1)

            if port_val is None:
                raise TimeoutError(f"Qt Agent port file '{port_file_path}' was not created within {timeout}s. Last error: {last_err}")
            port = port_val

        # Connect and verify with ping
        last_conn_err = None
        while time.time() < deadline:
            try:
                self._rpc_client = xmlrpc.client.ServerProxy(f"http://127.0.0.1:{port}", allow_none=True)
                self._rpc_client.ping()
                return
            except Exception as e:
                last_conn_err = e
                time.sleep(0.1)

        raise ConnectionError(f"Failed to connect to Qt Agent at 127.0.0.1:{port} within {timeout}s: {last_conn_err}")

    def disconnect(self):
        self._rpc_client = None

    def find_element(self, locator, **kwargs):
        if not self._rpc_client.find_widget(locator):
            raise ValueError(f"Widget matching '{locator}' not found.")
        return locator

    def click(self, element, button="left", x=-1, y=-1, double=False):
        self._rpc_client.click(element, button, x, y, double)

    def get_value(self, element):
        return self._rpc_client.get_property(element, 'text')

    def set_value(self, element, value):
        self._rpc_client.set_property(element, 'text', value)

    def key_clicks(self, element, text, delay_ms=-1):
        self._rpc_client.key_clicks(element, text, delay_ms)

    def press_key(self, element, key, modifiers=""):
        self._rpc_client.press_key(element, key, modifiers)

    def clear_text(self, element):
        self._rpc_client.clear_text(element)

    def get_property(self, element, property_name):
        return self._rpc_client.get_property(element, property_name)

    def set_property(self, element, property_name, value):
        return self._rpc_client.set_property(element, property_name, value)

    def select_tab(self, element, tab):
        return self._rpc_client.select_tab(element, tab)

    def select_combo_item(self, element, item):
        return self._rpc_client.select_combo_item(element, item)

    def dump_tree(self, root_locator=None):
        return self._rpc_client.dump_tree(root_locator)

    def close_app(self):
        if self._rpc_client:
            try:
                self._rpc_client.close_app()
            except Exception:
                pass
            self.disconnect()
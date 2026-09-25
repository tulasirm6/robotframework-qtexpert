"""
Injected C++ Agent Backend using LD_PRELOAD (libqt_test_agent.so).
Connects to embedded QTcpServer running on the Qt GUI main thread.
"""

from typing import Optional, Dict, Any, Union
from .base import BaseBackend
from ..client import QtAgentClient
from ..locators import parse_locator

class PreloadBackend(BaseBackend):
    def __init__(self, host: str = "127.0.0.1", port: int = 9988):
        self.host = host
        self.port = port
        self.client = QtAgentClient(host=host, port=port)

    def connect(self, host: Optional[str] = None, port: Optional[int] = None, timeout: float = 10.0, **kwargs):
        if host:
            self.host = host
            self.client.host = host
        if port:
            self.port = int(port)
            self.client.port = int(port)

        self.client.connect(retry_seconds=timeout)

    def disconnect(self):
        self.client.disconnect()

    def find_element(self, locator: Union[str, Dict[str, Any]], **kwargs):
        target = parse_locator(locator)
        res = self.client.send_command("exists", target=target)
        if not res.get("exists", False):
            raise ValueError(f"Widget matching '{locator}' does not exist.")
        return target

    def click(self, element: Union[str, Dict[str, Any]], button: str = "left", x: int = -1, y: int = -1, double: bool = False):
        target = parse_locator(element)
        self.client.send_command("click", target=target, button=button, x=x, y=y, double=double)

    def get_value(self, element: Union[str, Dict[str, Any]]):
        target = parse_locator(element)
        res = self.client.send_command("getProperty", target=target, propertyName="text")
        val = res.get("value")
        return str(val) if val is not None else ""

    def set_value(self, element: Union[str, Dict[str, Any]], value: str):
        target = parse_locator(element)
        self.client.send_command("clearText", target=target)
        self.client.send_command("keyClicks", target=target, text=value, delayMs=-1)

    def key_clicks(self, element: Union[str, Dict[str, Any]], text: str, delay_ms: int = -1):
        target = parse_locator(element)
        self.client.send_command("keyClicks", target=target, text=text, delayMs=delay_ms)

    def press_key(self, element: Union[str, Dict[str, Any]], key: str, modifiers: str = ""):
        target = parse_locator(element)
        self.client.send_command("keyPress", target=target, keyName=key, modifiers=modifiers)

    def clear_text(self, element: Union[str, Dict[str, Any]]):
        target = parse_locator(element)
        self.client.send_command("clearText", target=target)

    def get_property(self, element: Union[str, Dict[str, Any]], property_name: str):
        target = parse_locator(element)
        res = self.client.send_command("getProperty", target=target, property=property_name, propertyName=property_name)
        return res.get("value")

    def set_property(self, element: Union[str, Dict[str, Any]], property_name: str, value: Any):
        target = parse_locator(element)
        self.client.send_command("setProperty", target=target, property=property_name, propertyName=property_name, value=value)

    def select_tab(self, element: Union[str, Dict[str, Any]], tab: Union[str, int]):
        target = parse_locator(element)
        self.client.send_command("selectTab", target=target, tab=str(tab))

    def select_combo_item(self, element: Union[str, Dict[str, Any]], item: Union[str, int]):
        target = parse_locator(element)
        self.client.send_command("selectComboItem", target=target, item=str(item))

    def dump_tree(self, root_locator: Optional[Union[str, Dict[str, Any]]] = None):
        target = parse_locator(root_locator) if root_locator else {}
        res = self.client.send_command("dumpTree", target=target)
        return res.get("tree", {})

    def get_coverage(self):
        return self.client.get_coverage()

    def close_app(self):
        self.disconnect()

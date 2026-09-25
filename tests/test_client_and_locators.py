import unittest
import socket
import threading
import json
import time

from robotframework_qtexpert.locators import parse_locator
from robotframework_qtexpert.client import QtAgentClient

class TestLocatorParser(unittest.TestCase):
    def test_single_object_name(self):
        self.assertEqual(parse_locator("loginButton"), {"objectName": "loginButton"})

    def test_key_value_name(self):
        self.assertEqual(parse_locator("name=loginButton"), {"objectName": "loginButton"})
        self.assertEqual(parse_locator("objectName=submit"), {"objectName": "submit"})

    def test_multi_attribute(self):
        loc = 'type=QPushButton text="Click Me" visible=true'
        parsed = parse_locator(loc)
        self.assertEqual(parsed.get("className"), "QPushButton")
        self.assertEqual(parsed.get("text"), "Click Me")
        self.assertEqual(parsed.get("visible"), True)

    def test_dict_input(self):
        raw = {"type": "QLineEdit", "text": "foo", "visible": "true"}
        parsed = parse_locator(raw)
        self.assertEqual(parsed.get("className"), "QLineEdit")
        self.assertEqual(parsed.get("text"), "foo")
        self.assertEqual(parsed.get("visible"), True)


class TestClientProtocol(unittest.TestCase):
    def setUp(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(("127.0.0.1", 0))
        self.server_sock.listen(1)
        self.port = self.server_sock.getsockname()[1]
        self.running = True

        def echo_server():
            conn, _ = self.server_sock.accept()
            while self.running:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    req = json.loads(data.decode("utf-8").strip())
                    action = req.get("action")
                    if action == "ping":
                        resp = {"status": "ok"}
                    elif action == "click":
                        resp = {"status": "ok", "clicked": req.get("target")}
                    else:
                        resp = {"status": "error", "message": "unknown action"}
                    conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                except Exception:
                    break
            conn.close()

        self.thread = threading.Thread(target=echo_server, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.running = False
        self.server_sock.close()

    def test_ping_and_command(self):
        client = QtAgentClient(host="127.0.0.1", port=self.port, timeout=2.0)
        client.connect(retry_seconds=2.0)
        self.assertTrue(client.is_connected())

        ping_res = client.ping()
        self.assertEqual(ping_res.get("status"), "ok")

        click_res = client.send_command("click", target={"objectName": "btn"})
        self.assertEqual(click_res.get("status"), "ok")
        self.assertEqual(click_res.get("clicked"), {"objectName": "btn"})

        client.disconnect()
        self.assertFalse(client.is_connected())

if __name__ == '__main__':
    unittest.main()

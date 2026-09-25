"""
TCP Client for communicating with the injected Qt5 Test Agent (libqt_test_agent.so).
"""

import socket
import json
import time
from typing import Dict, Any, Optional

class QtAgentClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9988, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._buffer = b""

    def connect(self, retry_seconds: float = 5.0):
        """Connects to the Qt agent, retrying until timeout expires."""
        deadline = time.time() + retry_seconds
        last_err = None

        while time.time() < deadline:
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
                self.sock.settimeout(self.timeout)
                self._buffer = b""
                # Ping to verify readiness
                self.ping()
                return
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                time.sleep(0.1)

        raise ConnectionError(
            f"Failed to connect to Qt Agent at {self.host}:{self.port} within {retry_seconds}s. Last error: {last_err}"
        )

    def disconnect(self):
        """Closes the socket connection."""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self.sock.close()
                self.sock = None
                self._buffer = b""

    def is_connected(self) -> bool:
        return self.sock is not None

    def send_command(self, action: str, target: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Sends a JSON-RPC command to the Qt agent and returns the response."""
        if not self.sock:
            raise ConnectionError("Not connected to Qt Agent. Call connect() first.")

        payload = {
            "action": action,
            "target": target or {},
            **kwargs
        }
        msg = (json.dumps(payload) + "\n").encode("utf-8")
        self.sock.sendall(msg)

        # Read newline-delimited response
        while b"\n" not in self._buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionResetError("Connection lost while reading from Qt Agent.")
            self._buffer += chunk

        line, self._buffer = self._buffer.split(b"\n", 1)
        response = json.loads(line.decode("utf-8"))

        if response.get("status") != "ok":
            error_msg = response.get("message", f"Command '{action}' failed")
            raise RuntimeError(f"Qt Agent Error [{action}]: {error_msg}")

        return response

    def ping(self) -> Dict[str, Any]:
        return self.send_command("ping")

    def get_coverage(self) -> Dict[str, Any]:
        """Retrieves UI screen and control coverage statistics from the Qt Agent."""
        return self.send_command("getCoverage")

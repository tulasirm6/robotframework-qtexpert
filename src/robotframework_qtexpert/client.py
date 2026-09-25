"""
TCP Client for communicating with the injected Qt5 Test Agent (libqt_test_agent.so).
Supports thread-safe RPC commands and asynchronous event dispatching for live hover/inspect.
"""

import socket
import json
import time
import threading
import queue
from typing import Dict, Any, Optional, Callable, List

class QtAgentClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9988, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._buffer = b""
        self._event_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._response_queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def register_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Registers a callback for asynchronous server events (e.g. hoverWidget, pickWidget)."""
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)

    def unregister_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregisters an asynchronous event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def connect(self, retry_seconds: float = 5.0):
        """Connects to the Qt agent, retrying until timeout expires."""
        deadline = time.time() + retry_seconds
        last_err = None

        while time.time() < deadline:
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
                self.sock.settimeout(None)  # Use blocking mode in reader thread
                self._buffer = b""
                self._running = True
                self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
                self._reader_thread.start()
                # Ping to verify readiness
                self.ping()
                return
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                time.sleep(0.1)

        raise ConnectionError(
            f"Failed to connect to Qt Agent at {self.host}:{self.port} within {retry_seconds}s. Last error: {last_err}"
        )

    def _reader_loop(self):
        """Background thread reading newline-delimited JSON messages from the agent."""
        while self._running and self.sock:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                self._buffer += chunk
                while b"\n" in self._buffer:
                    line, self._buffer = self._buffer.split(b"\n", 1)
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue
                    try:
                        msg = json.loads(line_str)
                    except Exception:
                        continue

                    # If the message has 'type', it is an asynchronous event
                    if "type" in msg:
                        for cb in list(self._event_callbacks):
                            try:
                                cb(msg)
                            except Exception:
                                pass
                    else:
                        # Otherwise it's a response to a command
                        self._response_queue.put(msg)
            except Exception:
                break
        self._running = False

    def disconnect(self):
        """Closes the socket connection."""
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self.sock.close()
                self.sock = None
                self._buffer = b""
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
            self._reader_thread = None

    def is_connected(self) -> bool:
        return self.sock is not None and self._running

    def send_command(self, action: str, target: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Sends a JSON-RPC command to the Qt agent and returns the response."""
        if not self.sock or not self._running:
            raise ConnectionError("Not connected to Qt Agent. Call connect() first.")

        payload = {
            "action": action,
            "target": target or {},
            **kwargs
        }
        msg = (json.dumps(payload) + "\n").encode("utf-8")
        with self._lock:
            # Drain any stale responses
            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                except queue.Empty:
                    break

            self.sock.sendall(msg)

            try:
                response = self._response_queue.get(timeout=self.timeout)
            except queue.Empty:
                raise TimeoutError(f"Qt Agent command '{action}' timed out after {self.timeout}s")

        if response.get("status") != "ok":
            error_msg = response.get("message", f"Command '{action}' failed")
            raise RuntimeError(f"Qt Agent Error [{action}]: {error_msg}")

        return response

    def ping(self) -> Dict[str, Any]:
        return self.send_command("ping")

    def get_coverage(self) -> Dict[str, Any]:
        """Retrieves UI screen and control coverage statistics from the Qt Agent."""
        return self.send_command("getCoverage")

import os
import sys
import subprocess
import time
from robot.api import logger
from ._keyword_base import _KeywordBase

class ApplicationKeywords(_KeywordBase):
    def launch_application(
        self,
        command,
        mode=None,
        window_title=None,
        port_file_path=None,
        agent_so_path=None,
        port=None,
        timeout=15.0
    ):
        """
        Launches the target Qt application and connects to it using the specified mode.
        Modes: 'agent' (in-process), 'preload' / 'binary' (LD_PRELOAD C++ agent), or 'a11y' (accessibility).
        """
        if self._lib._backend:
            self.close_application()

        target_mode = (mode or self._lib._mode or 'auto').lower()
        logger.info(f"Launching application in '{target_mode}' mode: {command}")
        
        env = os.environ.copy()
        timeout = float(timeout)

        # Ensure Linux GUI processes connect to Xvfb display :99 if DISPLAY is not set
        if sys.platform.startswith("linux") and "DISPLAY" not in env:
            env["DISPLAY"] = ":99"

        # Forward current library's root directory to child process PYTHONPATH
        pkg_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cur_pythonpath = env.get("PYTHONPATH", "")
        if pkg_root not in cur_pythonpath:
            env["PYTHONPATH"] = f"{pkg_root}:{cur_pythonpath}".strip(":")

        # 1. PRELOAD / INJECTION MODE
        if target_mode in ('preload', 'binary'):
            so_path = agent_so_path or env.get('QT_AGENT_SO')
            if not so_path:
                # Auto-discover bundled or local build libqt_test_agent.so
                pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                candidates = [
                    os.path.join(pkg_dir, "bin", "libqt_test_agent.so"),
                    os.path.join(os.getcwd(), "cpp_agent", "build", "libqt_test_agent.so"),
                    os.path.join(os.getcwd(), "dist", "libqt_test_agent.so"),
                    "/usr/local/lib/libqt_test_agent.so",
                    "/usr/lib/libqt_test_agent.so",
                ]
                for c in candidates:
                    if os.path.exists(c):
                        so_path = c
                        break

            if not so_path or not os.path.exists(so_path):
                raise FileNotFoundError(
                    f"Agent shared library (libqt_test_agent.so) not found. "
                    "Build it using './build_agent.sh' or specify 'agent_so_path'."
                )

            so_path = os.path.abspath(so_path)
            current_preload = env.get("LD_PRELOAD", "")
            env["LD_PRELOAD"] = f"{so_path}:{current_preload}".strip(":")
            agent_port = int(port or 9988)
            env["QT_AGENT_PORT"] = str(agent_port)

            import shlex
            if isinstance(command, str):
                cmd_list = shlex.split(command)
            else:
                cmd_list = list(command)

            logger.info(f"Starting preload process: {cmd_list} with LD_PRELOAD={so_path}")
            self._lib._app_process = subprocess.Popen(cmd_list, shell=False, env=env)
            self._lib._backend = self._lib._ensure_backend(mode='preload', port=agent_port)
            self._lib.backend.connect(port=agent_port, timeout=timeout)
            logger.info("Successfully connected to Injected Qt Agent.")
            return

        # 2. IN-PROCESS AGENT MODE
        if target_mode == 'agent':
            if not port_file_path and not port:
                raise ValueError("Agent mode requires 'port_file_path' or 'port'.")

            if port_file_path and os.path.exists(port_file_path):
                try:
                    os.remove(port_file_path)
                except OSError:
                    pass

            if port_file_path:
                env['QT_AGENT_PORT_FILE'] = port_file_path

            self._lib._app_process = subprocess.Popen(command, shell=isinstance(command, str), env=env)
            self._lib._backend = self._lib._ensure_backend(mode='agent')
            self._lib.backend.connect(port_file_path=port_file_path, port=port, timeout=timeout)
            logger.info("Successfully connected to In-Process Qt Agent.")
            return

        # 3. ACCESSIBILITY MODE
        if target_mode == 'a11y':
            if not window_title and sys.platform.startswith('win') is False:
                raise ValueError("A11y mode requires 'window_title'.")

            # Enable Qt accessibility on Linux
            if sys.platform.startswith('linux'):
                env['QT_LINUX_ACCESSIBILITY_ALWAYS_ON'] = '1'
                env['QT_ACCESSIBILITY'] = '1'

            self._lib._app_process = subprocess.Popen(command, shell=isinstance(command, str), env=env)
            self._lib._backend = self._lib._ensure_backend(mode='a11y')
            self._lib.backend.connect(app_path=command, window_title=window_title, timeout=timeout)
            logger.info("Successfully connected via Accessibility.")
            return

        # 4. AUTO MODE
        if port_file_path:
            self.launch_application(command, mode='agent', port_file_path=port_file_path, timeout=timeout)
        elif agent_so_path or os.environ.get('QT_AGENT_SO'):
            self.launch_application(command, mode='preload', agent_so_path=agent_so_path, port=port, timeout=timeout)
        else:
            self.launch_application(command, mode='a11y', window_title=window_title, timeout=timeout)

    def start_application_with_qt_agent(self, application_path, agent_so_path, arguments="", port=9988, timeout=10.0):
        """Squish-compatible alias: launches application with C++ agent injected via LD_PRELOAD."""
        cmd = f"{application_path} {arguments}".strip()
        self.launch_application(cmd, mode='preload', agent_so_path=agent_so_path, port=port, timeout=timeout)

    def connect_to_qt_agent(self, host='127.0.0.1', port=9988, timeout=10.0):
        """Connects to an already running Qt application that has the agent running."""
        self._lib._backend = self._lib._ensure_backend(mode='preload', host=host, port=port)
        self._lib.backend.connect(host=host, port=port, timeout=float(timeout))
        logger.info(f"Connected to Qt Agent at {host}:{port}.")

    def connect_to_application(self, mode='agent', **kwargs):
        """Connects to an existing application without launching a new process."""
        self._lib._backend = self._lib._ensure_backend(mode=mode, **kwargs)
        self._lib.backend.connect(**kwargs)

    def close_application(self):
        """Closes the connection and terminates the application process."""
        if self._lib._backend:
            try:
                self._lib.backend.close_app()
            except Exception as e:
                logger.debug(f"close_app warning: {e}")
            try:
                self._lib.backend.disconnect()
            except Exception as e:
                logger.debug(f"disconnect warning: {e}")
            self._lib._backend = None

        if self._lib._app_process:
            logger.info("Terminating application process...")
            if self._lib._app_process.poll() is None:
                self._lib._app_process.terminate()
                try:
                    self._lib._app_process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self._lib._app_process.kill()
            self._lib._app_process = None
            logger.info("Application process terminated.")
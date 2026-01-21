import os
import subprocess
from ._keyword_base import _KeywordBase

class ApplicationKeywords(_KeywordBase):
    def launch_application(self, command, mode=None, window_title=None, port_file_path=None):
        if self._lib._backend: self.close_application()
        target_mode = mode or self._lib._mode
        logger.info(f"Launching in '{target_mode}' mode.")
        env = os.environ.copy()
        if target_mode == 'agent':
            if not port_file_path: raise ValueError("Agent mode requires 'port_file_path'.")
            env['QT_AGENT_PORT_FILE'] = port_file_path
        self._lib._app_process = subprocess.Popen(command, shell=True, env=env)
        if target_mode == 'agent':
            self._lib._backend = self._lib._ensure_backend(mode='agent', port_file_path=port_file_path)
        elif target_mode == 'a11y':
            if not window_title: raise ValueError("A11y mode requires 'window_title'.")
            self._lib._backend = self._lib._ensure_backend(mode='a11y')
            self._lib.backend.connect(app_path=command, window_title=window_title)

    def close_application(self):
        if not self._lib._backend: return
        self._lib.backend.close_app()
        self._lib.backend.disconnect()
        if self._lib._app_process and self._lib._app_process.poll() is None:
            self._lib._app_process.terminate()
        self._lib._backend = None
        self._lib._app_process = None
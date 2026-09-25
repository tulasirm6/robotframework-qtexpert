import sys
import os
from .base import BaseBackend

def get_backend(mode='auto', **kwargs):
    mode_lower = (mode or 'auto').lower()

    if mode_lower == 'agent':
        from .agent_client import AgentBackend
        return AgentBackend()

    if mode_lower in ('preload', 'binary', 'injected'):
        from .preload import PreloadBackend
        host = kwargs.get('host', '127.0.0.1')
        port = kwargs.get('port', 9988)
        return PreloadBackend(host=host, port=port)

    if mode_lower == 'a11y':
        if sys.platform.startswith('win'):
            from .a11y_win import WinA11yBackend
            return WinA11yBackend()
        if sys.platform.startswith('linux'):
            from .a11y_linux import LinuxA11yBackend
            return LinuxA11yBackend()
        if sys.platform == 'darwin':
            from .a11y_macos import MacA11yBackend
            return MacA11yBackend()
        raise NotImplementedError(f"Accessibility mode not supported on {sys.platform}")

    if mode_lower == 'auto':
        port_file = kwargs.get('port_file_path')
        if port_file and os.path.exists(port_file):
            try:
                from .agent_client import AgentBackend
                backend = AgentBackend()
                backend.connect(port_file_path=port_file, timeout=2.0)
                return backend
            except Exception:
                pass

        agent_so = kwargs.get('agent_so_path')
        if agent_so and os.path.exists(agent_so):
            from .preload import PreloadBackend
            return PreloadBackend()

        return get_backend(mode='a11y')

    raise ValueError(f"Unknown mode: {mode}")
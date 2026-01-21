import sys
import os
from .base import BaseBackend
from .agent_client import AgentBackend
from .a11y_win import WinA11yBackend
from .a11y_linux import LinuxA11yBackend
from .a11y_macos import MacA11yBackend

def get_backend(mode='auto', **kwargs):
    if mode == 'agent':
        return AgentBackend()
    
    if mode == 'a11y':
        if sys.platform == 'win32': return WinA11yBackend()
        if sys.platform == 'linux': return LinuxA11yBackend()
        if sys.platform == 'darwin': return MacA11yBackend()
        raise NotImplementedError(f"Accessibility mode not supported on {sys.platform}")

    if mode == 'auto':
        port_file = kwargs.get('port_file_path')
        if port_file and os.path.exists(port_file):
            try:
                backend = AgentBackend()
                backend.connect(port_file_path=port_file)
                return backend
            except Exception: pass
        return get_backend(mode='a11y')

    raise ValueError(f"Unknown mode: {mode}")
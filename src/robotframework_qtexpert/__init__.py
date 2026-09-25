import sys
from robot.api import logger

from .backends import get_backend
from .keywords.application import ApplicationKeywords
from .keywords.generic import GenericKeywords

__version__ = "2.0.0"

class qtexpert:
    """
    A unified Robot Framework library for testing Qt applications.
    Supports Injected C++ Agent (LD_PRELOAD / Squish alternative),
    In-Process Thread-Safe Python Agent, and Native Accessibility (A11y).
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self, mode='auto', default_host='127.0.0.1', default_port=9988):
        """
        Initializes qtexpert.
        
        Args:
            mode: The backend mode to use: 'preload'/'binary', 'agent', 'a11y', or 'auto' (default).
            default_host: Default host for agent socket connection (default: 127.0.0.1).
            default_port: Default port for agent connection (default: 9988).
        """
        self._mode = mode
        self._default_host = default_host
        self._default_port = int(default_port)
        self._backend = None
        self._app_process = None
        
        self.app = ApplicationKeywords(self)
        self.generic = GenericKeywords(self)
        
        logger.info(f"qtexpert initialized in '{mode}' mode (host={default_host}, port={default_port}).")

    def _ensure_backend(self, mode=None, **kwargs):
        target_mode = mode or self._mode
        if not self._backend:
            merged_kwargs = {
                'host': self._default_host,
                'port': self._default_port,
                **kwargs
            }
            self._backend = get_backend(mode=target_mode, **merged_kwargs)
        return self._backend

    @property
    def backend(self):
        if not self._backend:
            raise RuntimeError("Not connected to application. Use 'Launch Application' or 'Connect To Application' first.")
        return self._backend

    def get_keyword_names(self):
        names = []
        for group in [self.app, self.generic]:
            for attr in dir(group):
                if not attr.startswith('_') and callable(getattr(group, attr)):
                    names.append(attr)
        return names

    def get_keyword_arguments(self, name):
        import inspect
        normalized = name.lower().replace(" ", "_")
        for group in [self.app, self.generic]:
            func = getattr(group, normalized, getattr(group, name, None))
            if func and callable(func):
                sig = inspect.signature(func)
                args = []
                for p in sig.parameters.values():
                    if p.name == 'self':
                        continue
                    if p.kind == inspect.Parameter.VAR_POSITIONAL:
                        args.append(f"*{p.name}")
                    elif p.kind == inspect.Parameter.VAR_KEYWORD:
                        args.append(f"**{p.name}")
                    elif p.default != inspect.Parameter.empty:
                        args.append(f"{p.name}={p.default!r}")
                    else:
                        args.append(p.name)
                return args
        return ['*args', '**kwargs']

    def get_keyword_documentation(self, name):
        normalized = name.lower().replace(" ", "_")
        for group in [self.app, self.generic]:
            func = getattr(group, normalized, getattr(group, name, None))
            if func and callable(func) and func.__doc__:
                return func.__doc__
        return ""

    def run_keyword(self, name, args, kwargs):
        normalized = name.lower().replace(" ", "_")
        try:
            for group in [self.app, self.generic]:
                if hasattr(group, normalized):
                    return getattr(group, normalized)(*args, **kwargs)
                elif hasattr(group, name):
                    return getattr(group, name)(*args, **kwargs)
            raise AttributeError(f"Keyword '{name}' not found.")
        except Exception as e:
            logger.error(f"Keyword '{name}' failed: {e}")
            raise

# Library aliases for backward compatibility and drop-in replacements
robotframework_qtexpert = qtexpert
Qt5Library = qtexpert
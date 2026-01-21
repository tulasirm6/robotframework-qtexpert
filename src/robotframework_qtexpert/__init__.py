import sys
from robot.api import logger

from .backends import get_backend
from .keywords.application import ApplicationKeywords
from .keywords.generic import GenericKeywords

__version__ = "0.1.0"

class qtexpert:
    """
    A unified Robot Framework library for testing Qt applications.
    Supports both Agent and Accessibility modes.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self, mode='auto'):
        """
        Initializes the qtexpert.
        
        Args:
            mode: The backend mode to use. 'agent', 'a11y', or 'auto' (default).
        """
        self._mode = mode
        self._backend = None
        self._app_process = None
        
        self.app = ApplicationKeywords(self)
        self.generic = GenericKeywords(self)
        
        logger.info(f"QTexpert initialized in '{mode}' mode.")

    def _ensure_backend(self, **kwargs):
        if not self._backend:
            self._backend = get_backend(mode=self._mode, **kwargs)
        return self._backend

    @property
    def backend(self):
        if not self._backend:
            raise RuntimeError("Not connected. Use 'Launch Application' or 'Connect To Application' first.")
        return self._backend

    def get_keyword_names(self):
        return [name for group in [self.app, self.generic] for name in dir(group) if not name.startswith('_')]

    def run_keyword(self, name, args, kwargs):
        try:
            for group in [self.app, self.generic]:
                if hasattr(group, name):
                    return getattr(group, name)(*args, **kwargs)
            raise AttributeError(f"Keyword '{name}' not found.")
        except Exception as e:
            logger.error(f"Keyword '{name}' failed: {e}")
            raise
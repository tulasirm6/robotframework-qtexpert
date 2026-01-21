# src/robotframework_qtexpert/keywords/_keyword_base.py
from robot.api import logger

class _KeywordBase:
    def __init__(self, lib):
        self._lib = lib

    def _log_widget_action(self, action, widget_name):
        logger.info(f"Performing '{action}' on widget '{widget_name}'.")
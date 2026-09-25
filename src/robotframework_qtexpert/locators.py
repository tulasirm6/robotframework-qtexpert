"""
Locator parser for Qt5/Qt6 widgets.
Supports key-value format (similar to Squish real names), e.g.:
- "objectName=submitButton"
- "name=submitButton"
- "type=QPushButton text=Submit"
- "className=QLineEdit name=usernameInput"
- "text=Login"
- "window='MainWindow' visible=true"
- Direct widget name string fallback: "submitButton"
"""

import re
from typing import Dict, Any, Union

def parse_locator(locator: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parses a locator string or dictionary into target criteria for the Qt Agent.
    """
    if isinstance(locator, dict):
        return _normalize_keys(locator)

    if not isinstance(locator, str):
        raise ValueError(f"Locator must be string or dict, got {type(locator)}")

    locator = locator.strip()
    if not locator:
        return {}

    criteria: Dict[str, Any] = {}

    # Check if string contains key=value pairs (e.g. type=QPushButton text='Click Me')
    pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
    matches = re.findall(pattern, locator)

    if matches:
        for key, v1, v2, v3 in matches:
            val = v1 or v2 or v3
            # Handle booleans
            if val.lower() == 'true':
                val = True
            elif val.lower() == 'false':
                val = False
            criteria[key] = val
        return _normalize_keys(criteria)

    # Fallback: if no key=value syntax found, treat the string as objectName
    return {"objectName": locator}

def _normalize_keys(criteria: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}
    for k, v in criteria.items():
        lk = k.lower()
        if lk in ("name", "objectname"):
            normalized["objectName"] = v
        elif lk in ("type", "class", "classname"):
            normalized["className"] = v
        elif lk in ("text", "title"):
            normalized["text"] = v
        elif lk in ("window", "windowtitle"):
            normalized["windowTitle"] = v
        elif lk == "visible":
            normalized["visible"] = bool(v) if not isinstance(v, bool) else v
        elif lk == "enabled":
            normalized["enabled"] = bool(v) if not isinstance(v, bool) else v
        else:
            normalized[k] = v
    return normalized

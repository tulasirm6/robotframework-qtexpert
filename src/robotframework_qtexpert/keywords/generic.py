import time
import json
import os
from datetime import datetime
from typing import Union, Dict, Any, Optional

from robot.api import logger
from ._keyword_base import _KeywordBase

class GenericKeywords(_KeywordBase):
    # -------------------------------------------------------------
    # Standard Keywords (Backward-Compatible)
    # -------------------------------------------------------------
    def click_button(self, locator):
        """Clicks a button or widget identified by locator."""
        self._log_widget_action("Click", locator)
        element = self._lib.backend.find_element(locator)
        self._lib.backend.click(element)

    def input_text(self, locator, text):
        """Inputs text into the field identified by locator."""
        self._log_widget_action(f"Input Text '{text}'", locator)
        element = self._lib.backend.find_element(locator)
        self._lib.backend.set_value(element, text)

    def text_should_be(self, locator, expected_text):
        """Verifies that the text of the widget matches expected_text."""
        element = self._lib.backend.find_element(locator)
        actual_text = self._lib.backend.get_value(element)
        if actual_text != expected_text:
            raise AssertionError(f"Text for '{locator}' was '{actual_text}', expected '{expected_text}'")

    # -------------------------------------------------------------
    # Extended Squish-Style Keywords
    # -------------------------------------------------------------
    def click_object(self, locator: Union[str, Dict[str, Any]], button: str = "left", x: int = -1, y: int = -1):
        """
        Clicks on the widget identified by `locator`.
        Supports multi-criteria Squish locators (e.g., 'type=QPushButton text=Login').
        """
        self._log_widget_action(f"Click Object ({button})", locator)
        if hasattr(self._lib.backend, 'click'):
            self._lib.backend.click(locator, button=button, x=x, y=y, double=False)
        else:
            element = self._lib.backend.find_element(locator)
            self._lib.backend.click(element)

    def double_click_object(self, locator: Union[str, Dict[str, Any]]):
        """Double clicks on the widget identified by `locator`."""
        self._log_widget_action("Double Click", locator)
        if hasattr(self._lib.backend, 'click'):
            self._lib.backend.click(locator, button="left", double=True)
        else:
            element = self._lib.backend.find_element(locator)
            self._lib.backend.click(element)

    def right_click_object(self, locator: Union[str, Dict[str, Any]]):
        """Right clicks on the widget identified by `locator`."""
        self.click_object(locator, button="right")

    def type_text_into_object(self, locator: Union[str, Dict[str, Any]], text: str, delay_ms: int = -1):
        """Types text keystrokes into the widget using QTest key simulation."""
        self._log_widget_action(f"Type Text '{text}'", locator)
        if hasattr(self._lib.backend, 'key_clicks'):
            self._lib.backend.key_clicks(locator, text, delay_ms=delay_ms)
        else:
            element = self._lib.backend.find_element(locator)
            self._lib.backend.set_value(element, text)

    def clear_text(self, locator: Union[str, Dict[str, Any]]):
        """Clears text from input fields (QLineEdit, QTextEdit)."""
        self._log_widget_action("Clear Text", locator)
        if hasattr(self._lib.backend, 'clear_text'):
            self._lib.backend.clear_text(locator)
        else:
            element = self._lib.backend.find_element(locator)
            self._lib.backend.set_value(element, "")

    def clear_and_type_text(self, locator: Union[str, Dict[str, Any]], text: str):
        """Clears existing content and types new text."""
        self.clear_text(locator)
        self.type_text_into_object(locator, text)

    def press_key_on_object(self, locator: Union[str, Dict[str, Any]], key: str, modifiers: str = ""):
        """Sends key press (e.g. Return, Escape, Tab) with optional modifiers (Ctrl, Shift, Alt)."""
        self._log_widget_action(f"Press Key '{key}' [{modifiers}]", locator)
        if hasattr(self._lib.backend, 'press_key'):
            self._lib.backend.press_key(locator, key, modifiers)
        else:
            raise NotImplementedError("press_key is not supported by the current backend.")

    def get_object_property(self, locator: Union[str, Dict[str, Any]], property_name: str) -> Any:
        """Reads a Qt Q_PROPERTY or attribute."""
        if hasattr(self._lib.backend, 'get_property'):
            return self._lib.backend.get_property(locator, property_name)
        element = self._lib.backend.find_element(locator)
        if property_name == 'text':
            return self._lib.backend.get_value(element)
        raise NotImplementedError(f"Backend does not support get_property for '{property_name}'")

    def set_object_property(self, locator: Union[str, Dict[str, Any]], property_name: str, value: Any):
        """Sets a Qt property value."""
        self._log_widget_action(f"Set Property '{property_name}' = {value}", locator)
        if hasattr(self._lib.backend, 'set_property'):
            self._lib.backend.set_property(locator, property_name, value)
        elif property_name == 'text':
            element = self._lib.backend.find_element(locator)
            self._lib.backend.set_value(element, str(value))
        else:
            raise NotImplementedError("Current backend does not support arbitrary set_property.")

    def select_tab(self, locator: Union[str, Dict[str, Any]], tab: Union[str, int]):
        """
        Activates a tab page in a QTabWidget by title (e.g. 'Yard Operations') or 0-based index.
        """
        self._log_widget_action(f"Select Tab '{tab}'", locator)
        if hasattr(self._lib.backend, 'select_tab'):
            self._lib.backend.select_tab(locator, tab)
        else:
            raise NotImplementedError("Current backend does not support select_tab.")

    def text_should_contain(self, locator: Union[str, Dict[str, Any]], expected_substring: str):
        """Verifies that the text or content of the widget contains expected_substring."""
        actual_text = str(self.get_object_property(locator, 'text') or "")
        if str(expected_substring) not in actual_text:
            raise AssertionError(f"Text for '{locator}' was '{actual_text}', expected to contain '{expected_substring}'")

    def select_radio_button(self, locator: Union[str, Dict[str, Any]]):
        """Selects a radio button (QRadioButton) by clicking on it."""
        self._log_widget_action("Select Radio Button", locator)
        self.click_object(locator)

    def radio_button_should_be_selected(self, locator: Union[str, Dict[str, Any]]):
        """Asserts that a radio button (QRadioButton) is selected/checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val not in ("true", "1"):
            raise AssertionError(f"Radio button '{locator}' was expected to be selected, but was not.")

    def radio_button_should_not_be_selected(self, locator: Union[str, Dict[str, Any]]):
        """Asserts that a radio button (QRadioButton) is NOT selected/checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val not in ("false", "0", ""):
            raise AssertionError(f"Radio button '{locator}' was expected NOT to be selected, but was selected.")

    def select_checkbox(self, locator: Union[str, Dict[str, Any]]):
        """Selects/checks a QCheckBox if it is not already checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val not in ("true", "1"):
            self._log_widget_action("Select Checkbox", locator)
            self.click_object(locator)

    def unselect_checkbox(self, locator: Union[str, Dict[str, Any]]):
        """Unselects/unchecks a QCheckBox if it is currently checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val in ("true", "1"):
            self._log_widget_action("Unselect Checkbox", locator)
            self.click_object(locator)

    def checkbox_should_be_checked(self, locator: Union[str, Dict[str, Any]]):
        """Asserts that a checkbox (QCheckBox) is checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val not in ("true", "1"):
            raise AssertionError(f"Checkbox '{locator}' was expected to be checked, but was not.")

    def checkbox_should_not_be_checked(self, locator: Union[str, Dict[str, Any]]):
        """Asserts that a checkbox (QCheckBox) is NOT checked."""
        val = str(self.get_object_property(locator, "checked")).lower()
        if val not in ("false", "0", ""):
            raise AssertionError(f"Checkbox '{locator}' was expected NOT to be checked, but was checked.")

    def select_combo_option(self, locator: Union[str, Dict[str, Any]], option: Union[str, int]):
        """Selects an item from a QComboBox by visible text or index."""
        self._log_widget_action(f"Select Combo Option '{option}'", locator)
        if hasattr(self._lib.backend, 'select_combo_item'):
            self._lib.backend.select_combo_item(locator, option)
        elif str(option).isdigit():
            self.set_object_property(locator, "currentIndex", int(option))
        else:
            self.set_object_property(locator, "currentText", str(option))

    def combo_option_should_be(self, locator: Union[str, Dict[str, Any]], expected_option: str):
        """Asserts that the currently selected QComboBox option matches expected_option."""
        actual = str(self.get_object_property(locator, "currentText")).strip()
        if actual != str(expected_option).strip():
            raise AssertionError(f"Combo box '{locator}' selected option was '{actual}', expected '{expected_option}'")

    def set_slider_value(self, locator: Union[str, Dict[str, Any]], value: int):
        """Sets the integer position/value of a QSlider."""
        self._log_widget_action(f"Set Slider Value {value}", locator)
        self.set_object_property(locator, "value", int(value))

    def slider_value_should_be(self, locator: Union[str, Dict[str, Any]], expected_value: int):
        """Asserts that a QSlider's current value matches expected_value."""
        actual = int(self.get_object_property(locator, "value"))
        if actual != int(expected_value):
            raise AssertionError(f"Slider '{locator}' value was {actual}, expected {expected_value}")

    def set_spinbox_value(self, locator: Union[str, Dict[str, Any]], value: int):
        """Sets the numeric value of a QSpinBox or QDoubleSpinBox."""
        self._log_widget_action(f"Set Spinbox Value {value}", locator)
        self.set_object_property(locator, "value", int(value))

    def spinbox_value_should_be(self, locator: Union[str, Dict[str, Any]], expected_value: int):
        """Asserts that a QSpinBox's current value matches expected_value."""
        actual = int(self.get_object_property(locator, "value"))
        if actual != int(expected_value):
            raise AssertionError(f"Spinbox '{locator}' value was {actual}, expected {expected_value}")

    def click_link(self, locator: Union[str, Dict[str, Any]], link_target: str = ""):
        """Clicks an HTML hyperlink embedded in a QLabel."""
        self._log_widget_action(f"Click Link '{link_target}'", locator)
        self.click_object(locator)

    def object_property_should_be(self, locator: Union[str, Dict[str, Any]], property_name: str, expected_value: Any):
        """Asserts that the object's property matches expected_value."""
        actual = self.get_object_property(locator, property_name)
        if str(actual) != str(expected_value):
            raise AssertionError(
                f"Property '{property_name}' on '{locator}' was '{actual}', expected '{expected_value}'"
            )

    def object_should_exist(self, locator: Union[str, Dict[str, Any]]):
        """Fails if the object does not exist."""
        try:
            self._lib.backend.find_element(locator)
        except Exception as e:
            raise AssertionError(f"Expected object '{locator}' to exist, but it was not found: {e}")

    def object_should_not_exist(self, locator: Union[str, Dict[str, Any]]):
        """Fails if the object exists."""
        try:
            self._lib.backend.find_element(locator)
            exists = True
        except Exception:
            exists = False
        if exists:
            raise AssertionError(f"Expected object '{locator}' NOT to exist, but it was found.")

    def wait_for_object(self, locator: Union[str, Dict[str, Any]], timeout: float = 10.0, poll_interval: float = 0.2):
        """Polls until the object exists and is ready."""
        deadline = time.time() + float(timeout)
        last_err = None
        while time.time() < deadline:
            try:
                self._lib.backend.find_element(locator)
                return True
            except Exception as e:
                last_err = e
            time.sleep(poll_interval)
        raise TimeoutError(f"Widget '{locator}' did not appear within {timeout}s. Last error: {last_err}")

    def wait_for_object_to_disappear(self, locator: Union[str, Dict[str, Any]], timeout: float = 10.0, poll_interval: float = 0.2):
        """Polls until the object disappears."""
        deadline = time.time() + float(timeout)
        while time.time() < deadline:
            try:
                self._lib.backend.find_element(locator)
            except Exception:
                return True
            time.sleep(poll_interval)
        raise TimeoutError(f"Widget '{locator}' still exists after {timeout}s.")

    def dump_object_tree(self, output_file: Optional[str] = None, root_locator: Optional[str] = None) -> Dict[str, Any]:
        """Dumps the full Qt widget hierarchy and properties (Object Spy)."""
        if hasattr(self._lib.backend, 'dump_tree'):
            tree = self._lib.backend.dump_tree(root_locator)
        else:
            raise NotImplementedError("Current backend does not support dump_object_tree.")

        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tree, f, indent=2)
            logger.info(f"UI Object Tree saved to: {output_file}")
        return tree

    def get_ui_coverage(self) -> Dict[str, Any]:
        """Returns interactive control coverage statistics from the Qt Agent."""
        if hasattr(self._lib.backend, 'get_coverage'):
            return self._lib.backend.get_coverage()
        return {"status": "unsupported"}

    def generate_ui_coverage_report(
        self,
        output_html: str = "results/coverage.html",
        output_json: Optional[str] = "results/coverage.json"
    ) -> Dict[str, Any]:
        """Generates an HTML and JSON UI Screen & Interactive Control Coverage Report."""
        cov = self.get_ui_coverage()
        if output_json:
            os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(cov, f, indent=2)

        os.makedirs(os.path.dirname(os.path.abspath(output_html)), exist_ok=True)
        html = self._render_coverage_html(cov)
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"UI Coverage Report generated: {output_html}")
        return cov

    def _render_coverage_html(self, data: Dict[str, Any]) -> str:
        overall = data.get("overall", {})
        total_ctrls = overall.get("totalControls", 0)
        exercised_ctrls = overall.get("exercisedControls", 0)
        pct = overall.get("coverageRate", 0.0)
        screens = data.get("screens", [])

        bar_color = "#34d399" if pct >= 80 else ("#fbbf24" if pct >= 50 else "#f87171")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        screens_html = []
        for s in screens:
            s_name = s.get("screenName", "Unknown View")
            s_tot = s.get("total", 0)
            s_ex = s.get("exercised", 0)
            s_pct = s.get("coverageRate", 0.0)
            s_badge_color = "#34d399" if s_pct >= 80 else ("#fbbf24" if s_pct >= 50 else "#f87171")

            rows = []
            for c in s.get("exercisedControls", []):
                rows.append(f"""
                <tr>
                    <td><span class="badge badge-success">Exercised</span></td>
                    <td><code>{c.get('type','')}</code></td>
                    <td><strong>{c.get('name','')}</strong></td>
                    <td class="italic">{c.get('text','')}</td>
                </tr>
                """)
            for c in s.get("unexercisedControls", []):
                rows.append(f"""
                <tr>
                    <td><span class="badge badge-muted">Untested</span></td>
                    <td><code>{c.get('type','')}</code></td>
                    <td><strong>{c.get('name','')}</strong></td>
                    <td class="italic">{c.get('text','')}</td>
                </tr>
                """)

            screens_html.append(f"""
            <div class="screen-card">
                <div class="screen-header">
                    <div class="screen-title">
                        <h3>{s_name}</h3>
                        <div class="screen-meta">{s_ex} of {s_tot} controls exercised</div>
                    </div>
                    <div class="screen-pct-badge" style="background: {s_badge_color}22; color: {s_badge_color};">
                        {s_pct:.1f}%
                    </div>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {s_pct}%; background: {s_badge_color};"></div>
                </div>
                <details class="controls-details">
                    <summary>View Controls Breakdown ({len(rows)} controls)</summary>
                    <table class="data-table">
                        <thead>
                            <tr><th>Status</th><th>Class</th><th>Name</th><th>Text</th></tr>
                        </thead>
                        <tbody>
                            {"".join(rows) if rows else '<tr><td colspan="4" class="text-dim">No interactive controls found.</td></tr>'}
                        </tbody>
                    </table>
                </details>
            </div>
            """)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Qt UI Coverage Report</title>
    <style>
        :root {{
            --bg: #0f172a; --surface: #1e293b; --surface-sub: #162032;
            --border: #334155; --text: #f8fafc; --text-dim: #94a3b8;
            --primary: #38bdf8; --success: #34d399; --warning: #fbbf24; --danger: #f87171;
            --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        body {{ background: var(--bg); color: var(--text); font-family: var(--font); padding: 32px 24px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; }}
        .grid-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }}
        .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
        .stat-label {{ font-size: 13px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }}
        .stat-val {{ font-size: 32px; font-weight: 800; }}
        .screen-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 14px; }}
        .screen-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .progress-bar-bg {{ background: rgba(255,255,255,0.08); border-radius: 9999px; height: 8px; width: 100%; margin: 10px 0; overflow: hidden; }}
        .progress-bar-fill {{ height: 100%; border-radius: 9999px; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        .data-table th, .data-table td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-success {{ background: rgba(52, 211, 153, 0.15); color: #34d399; }}
        .badge-muted {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; }}
        code {{ font-family: monospace; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h2>Qt5 UI Feature Coverage Report</h2>
                <div style="font-size: 13px; color: var(--text-dim);">{timestamp}</div>
            </div>
        </div>
        <div class="grid-stats">
            <div class="stat-card">
                <div class="stat-label">Total Coverage</div>
                <div class="stat-val" style="color: {bar_color};">{pct:.1f}%</div>
                <div style="font-size: 12px; color: var(--text-dim);">{exercised_ctrls} of {total_ctrls} controls</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Views / Screens</div>
                <div class="stat-val">{len(screens)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Exercised Controls</div>
                <div class="stat-val" style="color: var(--success);">{exercised_ctrls}</div>
            </div>
        </div>
        <div>
            <h3>Screen Breakdown</h3>
            {"".join(screens_html) if screens_html else '<p style="color: var(--text-dim); margin-top: 12px;">No screen data available.</p>'}
        </div>
    </div>
</body>
</html>"""
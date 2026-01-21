from ._keyword_base import _KeywordBase

class GenericKeywords(_KeywordBase):
    def click_button(self, locator):
        self._log_widget_action("Click", locator)
        element = self._lib.backend.find_element(locator)
        self._lib.backend.click(element)

    def input_text(self, locator, text):
        self._log_widget_action(f"Input Text '{text}'", locator)
        element = self._lib.backend.find_element(locator)
        self._lib.backend.set_value(element, text)

    def text_should_be(self, locator, expected_text):
        element = self._lib.backend.find_element(locator)
        actual_text = self._lib.backend.get_value(element)
        if actual_text != expected_text:
            raise AssertionError(f"Text for '{locator}' was '{actual_text}', expected '{expected_text}'")
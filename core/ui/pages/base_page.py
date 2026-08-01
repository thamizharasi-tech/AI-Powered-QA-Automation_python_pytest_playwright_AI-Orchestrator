"""
BasePage — Root Page Object Model
==================================
All page objects inherit from this class.

Provides production-standard Playwright wrappers with:
  - Explicit waits before every interaction
  - Configurable timeouts
  - scroll_into_view_if_needed() before click
  - clear() before fill() to prevent data appending
  - Meaningful error messages on failure
  - Full set of common UI interaction methods
"""

from playwright.sync_api import Page, Locator, expect


class BasePage:
    """Base class for all Page Object Model classes."""

    DEFAULT_TIMEOUT: int = 10_000   # 10 seconds
    SHORT_TIMEOUT:   int = 5_000    # 5 seconds — for quick visibility checks

    def __init__(self, page: Page) -> None:
        self.page = page

    # ── Core Interactions ─────────────────────────────────────────────────────

    def click(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element to be visible, scroll into view, then click.

        Parameters
        ----------
        locator : str   — CSS or XPath selector
        timeout : int   — milliseconds to wait for visibility (default 10s)
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.scroll_into_view_if_needed()
        element.click(timeout=timeout)

    def fill(self, locator: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element to be visible, clear existing content, then fill.

        Parameters
        ----------
        locator : str   — CSS or XPath selector
        value   : str   — text to enter
        timeout : int   — milliseconds to wait for visibility (default 10s)
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.clear()
        element.fill(value)

    def get_text(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Wait for element to be visible and return its text content.

        Returns empty string if element has no text content.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        return element.text_content() or ""

    def get_input_value(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Wait for input element to be visible and return its current value.

        Use this for <input>, <textarea>, and <select> elements.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        return element.input_value()

    def get_attribute(self, locator: str, attribute: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Wait for element to be visible and return the value of the given attribute.

        Returns empty string if attribute is not present.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        return element.get_attribute(attribute) or ""

    def select_option(self, locator: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for a <select> element to be visible and select an option by value.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.select_option(value)

    def hover(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element to be visible and hover over it.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.hover()

    def double_click(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element to be visible and double-click it.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.dblclick(timeout=timeout)

    def clear_and_type(self, locator: str, value: str, delay: int = 50,
                       timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element, clear it, then type character-by-character.

        Use this for autocomplete / typeahead inputs where fill() bypasses
        the input event listeners.

        Parameters
        ----------
        locator : str   — CSS or XPath selector
        value   : str   — text to type
        delay   : int   — milliseconds between keystrokes (default 50ms)
        timeout : int   — milliseconds to wait for visibility
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.clear()
        element.type(value, delay=delay)

    def press_key(self, locator: str, key: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for element to be visible and press a keyboard key.

        Parameters
        ----------
        key : str — e.g. "Enter", "Tab", "Escape", "ArrowDown"
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        element.press(key)

    # ── Visibility & State Checks ─────────────────────────────────────────────

    def is_visible(self, locator: str, timeout: int = SHORT_TIMEOUT) -> bool:
        """
        Return True if the element becomes visible within the timeout.
        Returns False (does NOT raise) if the element is not found or not visible.

        Parameters
        ----------
        timeout : int — milliseconds to wait (default 5s for quick checks)
        """
        try:
            self.page.locator(locator).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_enabled(self, locator: str, timeout: int = SHORT_TIMEOUT) -> bool:
        """
        Return True if the element is visible AND enabled (not disabled).
        """
        try:
            element = self.page.locator(locator)
            element.wait_for(state="visible", timeout=timeout)
            return element.is_enabled()
        except Exception:
            return False

    def is_checked(self, locator: str, timeout: int = SHORT_TIMEOUT) -> bool:
        """
        Return True if a checkbox or radio button is checked.
        """
        try:
            element = self.page.locator(locator)
            element.wait_for(state="visible", timeout=timeout)
            return element.is_checked()
        except Exception:
            return False

    # ── Wait Helpers ──────────────────────────────────────────────────────────

    def wait_for_element(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> Locator:
        """
        Wait for element to be visible and return the Playwright Locator.

        Use when you need the Locator object for further chaining.
        """
        element = self.page.locator(locator)
        element.wait_for(state="visible", timeout=timeout)
        return element

    def wait_for_url(self, url_pattern: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Wait for the page URL to match the given glob pattern.

        Parameters
        ----------
        url_pattern : str — glob pattern, e.g. "**/dashboard/**"
        """
        self.page.wait_for_url(url_pattern, timeout=timeout)

    def wait_for_load(self, state: str = "domcontentloaded") -> None:
        """
        Wait for the page to reach the given load state.

        Parameters
        ----------
        state : str — "domcontentloaded" | "load" | "networkidle"
                      Prefer "domcontentloaded" over "networkidle" for
                      apps with background polling (avoids timeout flakiness).
        """
        from typing import Literal
        _state: Literal["domcontentloaded", "load", "networkidle"] = (
            "domcontentloaded" if state == "domcontentloaded"
            else "networkidle" if state == "networkidle"
            else "load"
        )
        self.page.wait_for_load_state(_state)

    # ── Assertion Helpers ─────────────────────────────────────────────────────

    def assert_visible(self, locator: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert that the element is visible. Raises AssertionError if not.
        Uses Playwright's expect() for built-in retry logic.
        """
        expect(self.page.locator(locator)).to_be_visible(timeout=timeout)

    def assert_text(self, locator: str, expected_text: str,
                    timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert that the element contains the expected text.
        Uses Playwright's expect() for built-in retry logic.
        """
        expect(self.page.locator(locator)).to_contain_text(expected_text, timeout=timeout)

    def assert_value(self, locator: str, expected_value: str,
                     timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert that an input element has the expected value.
        Uses Playwright's expect() for built-in retry logic.
        """
        expect(self.page.locator(locator)).to_have_value(expected_value, timeout=timeout)

    def assert_url_contains(self, pattern: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert that the current page URL contains the given pattern.
        """
        expect(self.page).to_have_url(f"**{pattern}**", timeout=timeout)

    # ── Count Helpers ─────────────────────────────────────────────────────────

    def count_elements(self, locator: str) -> int:
        """
        Return the number of elements matching the locator.
        Does NOT wait — returns the current count immediately.
        """
        return self.page.locator(locator).count()

    # ── Role-based Locator Helpers (Playwright web-first) ─────────────────────
    # These use Playwright's built-in role/label/placeholder locators which are
    # more resilient to UI changes than XPath and CSS selectors.

    def click_by_role(self, role: str, name: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Click an element by its ARIA role and accessible name.

        More resilient than XPath — works regardless of CSS class changes.

        Parameters
        ----------
        role    : str — ARIA role, e.g. 'button', 'link', 'checkbox', 'radio'
        name    : str — accessible name (visible text or aria-label)
        timeout : int — milliseconds to wait (default 10s)

        Example
        -------
        self.click_by_role('button', 'Save')
        self.click_by_role('link', 'Add')
        """
        locator = self.page.get_by_role(role, name=name)
        locator.wait_for(state="visible", timeout=timeout)
        locator.scroll_into_view_if_needed()
        locator.click(timeout=timeout)

    def fill_by_label(self, label: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Fill an input field identified by its visible label text.

        Parameters
        ----------
        label   : str — visible label text, e.g. 'First Name', 'Username'
        value   : str — text to enter
        timeout : int — milliseconds to wait (default 10s)

        Example
        -------
        self.fill_by_label('First Name', 'Alice')
        """
        locator = self.page.get_by_label(label)
        locator.wait_for(state="visible", timeout=timeout)
        locator.clear()
        locator.fill(value)

    def fill_by_placeholder(self, placeholder: str, value: str,
                            timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Fill an input field identified by its placeholder text.

        Parameters
        ----------
        placeholder : str — placeholder text, e.g. 'Type for hints...'
        value       : str — text to enter
        timeout     : int — milliseconds to wait (default 10s)

        Example
        -------
        self.fill_by_placeholder('Type for hints...', 'John')
        """
        locator = self.page.get_by_placeholder(placeholder)
        locator.wait_for(state="visible", timeout=timeout)
        locator.clear()
        locator.fill(value)

    def assert_url_contains_pattern(self, pattern: str,
                                    timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert the current page URL matches a glob pattern.

        Uses Playwright's web-first expect() for built-in retry logic.

        Parameters
        ----------
        pattern : str — glob pattern, e.g. '**/viewPersonalDetails/**'
        timeout : int — milliseconds to wait (default 10s)

        Example
        -------
        self.assert_url_contains_pattern('**/viewPersonalDetails/**')
        """
        expect(self.page).to_have_url(pattern, timeout=timeout)

    def assert_page_title(self, title: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Assert the page <title> contains the given text.

        Uses Playwright's web-first expect() for built-in retry logic.

        Parameters
        ----------
        title   : str — expected title text (partial match)
        timeout : int — milliseconds to wait (default 10s)
        """
        expect(self.page).to_have_title(title, timeout=timeout)

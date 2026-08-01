"""
LoginPage — Page Object for the Login page.

Extends BasePage for all Playwright interactions.
Covers: login form, dashboard verification, error message retrieval.
"""

from playwright.sync_api import expect

from core.ui.pages.base_page import BasePage
from core.ui.locators.login_locator import LoginLocator


class LoginPage(BasePage):
    """Page Object for the OrangeHRM Login page."""

    def __init__(self, page) -> None:
        super().__init__(page)

    # ── Login Actions ─────────────────────────────────────────────────────────

    def enter_username(self, username: str) -> None:
        """Fill the Username field."""
        self.fill(LoginLocator.USERNAME, username)

    def enter_password(self, password: str) -> None:
        """Fill the Password field."""
        self.fill(LoginLocator.PASSWORD, password)

    def click_login(self) -> None:
        """Click the Login button."""
        self.click(LoginLocator.LOGIN_BUTTON)

    def login(self, username: str, password: str) -> None:
        """
        Enter credentials and submit the login form.

        Parameters
        ----------
        username : str — login username
        password : str — login password
        """
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    # ── Post-Login Verification ───────────────────────────────────────────────

    def verify_dashboard(self) -> None:
        """
        Assert the Dashboard navigation link is visible after login.

        Uses domcontentloaded (not networkidle) to avoid flakiness on
        apps with background polling requests (e.g. OrangeHRM).
        Raises PlaywrightAssertionError if the dashboard is not visible
        within 15 seconds.
        """
        self.page.wait_for_load_state("domcontentloaded")
        expect(
            self.page.locator(LoginLocator.DASHBOARD_TITLE)
        ).to_be_visible(timeout=15_000)

    # ── Error Message Retrieval ───────────────────────────────────────────────

    def get_error_message(self) -> str:
        """
        Return the login error message text.

        Returns the text content of the alert message shown when credentials
        are invalid (e.g. "Invalid credentials"). Returns an empty string if
        no error message is visible within 5 seconds.

        Returns
        -------
        str — error message text, or "" if not visible
        """
        try:
            self.page.locator(LoginLocator.ERROR_MESSAGE).wait_for(
                state="visible", timeout=5_000
            )
            return self.page.locator(LoginLocator.ERROR_MESSAGE).text_content() or ""
        except Exception:
            return ""

    def verify_error_message_visible(self) -> None:
        """
        Assert that the login error message is visible.

        Raises PlaywrightAssertionError if no error message appears
        within 5 seconds.
        """
        expect(
            self.page.locator(LoginLocator.ERROR_MESSAGE)
        ).to_be_visible(timeout=5_000)

    def verify_required_field_error(self) -> None:
        """
        Assert that a 'Required' field validation error is visible.

        Raises PlaywrightAssertionError if no Required error appears
        within 5 seconds.
        """
        expect(
            self.page.locator(LoginLocator.REQUIRED_ERROR)
        ).to_be_visible(timeout=5_000)

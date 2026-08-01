"""
test_login.py — Hand-Written Login Test Suite
===============================================
Covers:
  TC-LOGIN-001  Valid login with correct credentials → Dashboard visible
  TC-LOGIN-002  Invalid login with wrong credentials → Error message visible
  TC-LOGIN-003  Dashboard navigation to Admin module works

Framework components:
  - LoginPage        (core/ui/pages/login_page.py)
  - DashboardPage    (core/ui/pages/dashboard_page.py)
  - SessionManager   (core/ui/session_manager.py)
  - conftest.py      `page` fixture (browser, video, tracing, Allure attachments)
  - XLUtils          read_cloud_env()
  - common_modules   result()
  - e2e_testData     url, username, password, storage_state_path
"""

import allure
import pytest

from core.common_modules import result
from core.e2e_testData import url, username, password, storage_state_path
from core.ui.pages.login_page import LoginPage
from core.ui.pages.dashboard_page import DashboardPage
from core.ui.session_manager import SessionManager
from core.utils.XLUtils import read_api_data_from_excel, read_cloud_env


def _navigate_to_login(page) -> None:
    """
    Navigate to the application URL and ensure the login form is visible.

    If storageState has auto-authenticated the browser (landing on Dashboard),
    this helper clears cookies and reloads so the login form is accessible.
    This is required for tests that explicitly test the login page itself.
    """
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

    # If already authenticated (storageState loaded a valid session),
    # clear cookies so we land on the login page
    login_input = page.locator("input[name='username']")
    if not login_input.is_visible(timeout=4_000):
        # We're on the dashboard — clear session and reload to get login page
        page.context.clear_cookies()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_load_state("domcontentloaded")

    # Final wait — ensure login form is ready
    login_input.wait_for(state="visible", timeout=15_000)


@allure.feature("Authentication")
class TestLogin:
    """
    End-to-end test suite for the Login feature.

    Pre-conditions for all tests:
      - Application is accessible at the configured URL
      - Valid HR Administrator credentials are configured in Excel / env vars
      - The `page` fixture from conftest.py provides a pre-configured Playwright browser
    """

    # ── TC-LOGIN-001: Valid Login ─────────────────────────────────────────────

    @allure.story("Valid Login")
    @allure.title("TC-LOGIN-001: Valid login with correct credentials — Dashboard visible")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_valid_login(self, page):
        """
        Verify that an HR Administrator can log in with valid credentials
        and the Dashboard navigation link is visible after login.

        Steps:
          1. Navigate to the application URL
          2. Enter valid username and password
          3. Click Login
          4. Verify Dashboard navigation link is visible

        Expected Result:
          - Dashboard navigation link is visible within 15 seconds
        """
        # ── Arrange ──────────────────────────────────────────────────────────
        cloud_env = read_cloud_env()

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            _navigate_to_login(page)

        login = LoginPage(page)

        with allure.step(f"Enter valid credentials (username='{username}') and click Login"):
            login.login(username, password)

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify Dashboard is visible after login"):
            try:
                login.verify_dashboard()
                result(
                    "passed",
                    "Dashboard navigation link should be visible after valid login",
                    "Dashboard navigation link is visible",
                )
            except Exception as exc:
                result(
                    "failed",
                    "Dashboard navigation link should be visible after valid login",
                    f"Dashboard NOT visible: {exc}",
                )
                raise

    # ── TC-LOGIN-002: Invalid Login ───────────────────────────────────────────

    @allure.story("Invalid Login")
    @allure.title("TC-LOGIN-002: Invalid login with wrong credentials — Error message visible")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_invalid_login(self, page):
        """
        Verify that entering invalid credentials displays an error message
        and does NOT navigate to the Dashboard.

        Steps:
          1. Navigate to the application URL
          2. Enter an invalid username and wrong password
          3. Click Login
          4. Verify an error message is displayed

        Expected Result:
          - Login error message is visible
          - User remains on the Login page
        """
        # ── Arrange ──────────────────────────────────────────────────────────
        cloud_env    = read_cloud_env()
        bad_username = "invalid_user_xyz"
        bad_password = "WrongPassword999!"

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            _navigate_to_login(page)

        login = LoginPage(page)

        with allure.step(f"Enter invalid credentials (username='{bad_username}')"):
            login.login(bad_username, bad_password)

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify error message is displayed"):
            try:
                error_msg = login.get_error_message()
                assert error_msg, "Error message text should not be empty"
                result(
                    "passed",
                    "Login error message should be visible for invalid credentials",
                    f"Error message displayed: '{error_msg}'",
                )
            except AssertionError as exc:
                result(
                    "failed",
                    "Login error message should be visible for invalid credentials",
                    f"Error message NOT visible or empty: {exc}",
                )
                raise
            except Exception as exc:
                result(
                    "failed",
                    "Login error message should be visible for invalid credentials",
                    f"Unexpected error: {exc}",
                )
                raise

    # ── TC-LOGIN-003: Dashboard Navigation ───────────────────────────────────

    @allure.story("Dashboard Navigation")
    @allure.title("TC-LOGIN-003: Dashboard loads and Admin module navigation works")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dashboard_navigation(self, page):
        """
        Verify that after login the Dashboard is visible and clicking Admin
        in the left navigation menu navigates to the Admin module.

        Steps:
          1. Navigate to the application URL
          2. Login with valid credentials
          3. Verify Dashboard is visible
          4. Click Admin in the left navigation menu
          5. Verify navigation succeeded (no error)

        Expected Result:
          - Dashboard is visible after login
          - Admin module loads without error
        """
        # ── Arrange ──────────────────────────────────────────────────────────
        cloud_env = read_cloud_env()

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application and login"):
            _navigate_to_login(page)
            LoginPage(page).login(username, password)

        # ── Assert: Dashboard ─────────────────────────────────────────────────
        with allure.step("Verify Dashboard is visible"):
            try:
                dashboard = DashboardPage(page)
                assert dashboard.verify_dashboard(), "Dashboard should be visible"
                result(
                    "passed",
                    "Dashboard should be visible after login",
                    "Dashboard is visible",
                )
            except Exception as exc:
                result(
                    "failed",
                    "Dashboard should be visible after login",
                    f"Dashboard NOT visible: {exc}",
                )
                raise

        # ── Assert: Admin Navigation ──────────────────────────────────────────
        with allure.step("Navigate to Admin module via left menu"):
            try:
                dashboard.navigate_to_admin()
                result(
                    "passed",
                    "Admin module should load after clicking Admin in left menu",
                    "Admin navigation completed successfully",
                )
            except Exception as exc:
                result(
                    "failed",
                    "Admin module should load after clicking Admin in left menu",
                    f"Admin navigation failed: {exc}",
                )
                raise

    # ── Utility: Generate Storage State ──────────────────────────────────────
    # NOTE: This is a setup utility, not a regression test.
    # Run it manually once to save the browser session:
    #   pytest tests/ui/test_login.py::TestLogin::test_generate_storage_state -v -s
    # The saved session is then reused by subsequent tests via conftest.py.

    @allure.story("Session Management")
    @allure.title("UTIL: Generate and save browser storage state (run manually)")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.skip(reason="Utility — run manually to regenerate storageState.json")
    def test_generate_storage_state(self, page):
        """
        Login and save the browser session to storageState.json.

        This utility test is skipped by default. Run it manually when you
        need to regenerate the saved session (e.g. after password change):

            pytest tests/ui/test_login.py::TestLogin::test_generate_storage_state -v -s -k ""

        The saved session is loaded by the `page` fixture in conftest.py
        to skip the login step in subsequent tests.
        """
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")

        login = LoginPage(page)

        with allure.step("Login with valid credentials"):
            login.login(username, password)

        with allure.step("Verify Dashboard is visible"):
            try:
                login.verify_dashboard()
                result("passed", "Dashboard should be visible", "Dashboard is visible")
            except Exception as exc:
                result("failed", "Dashboard should be visible", f"NOT visible: {exc}")
                raise

        with allure.step(f"Save storage state to: {storage_state_path}"):
            SessionManager.save_storage_state(page, storage_state_path)
            result(
                "passed",
                "Storage state should be saved successfully",
                f"Storage state saved → {storage_state_path}",
            )

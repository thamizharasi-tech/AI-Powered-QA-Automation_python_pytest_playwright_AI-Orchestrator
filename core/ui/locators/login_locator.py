"""
LoginLocator — Element selectors for the Login page.

Design principles:
  - URL-based locators are preferred over text-based ones (language-agnostic)
  - All selectors verified against OrangeHRM OS 5.9
"""

from playwright.sync_api import Page


class LoginLocator:
    """Static CSS / XPath selectors for the Login page."""

    # ── Login Form ────────────────────────────────────────────────────────────
    USERNAME        = "input[name='username']"
    PASSWORD        = "input[name='password']"
    LOGIN_BUTTON    = "button[type='submit']"

    # ── Post-Login Verification ───────────────────────────────────────────────
    # URL-based — language-agnostic (works regardless of OrangeHRM locale setting)
    DASHBOARD_TITLE = "//a[@href='/web/index.php/dashboard/index']"

    # ── Error Messages ────────────────────────────────────────────────────────
    # Shown when credentials are invalid
    ERROR_MESSAGE   = "//p[contains(@class,'oxd-alert-content-text')]"
    # Shown when a required field is left empty on submit
    REQUIRED_ERROR  = "//span[text()='Required']"

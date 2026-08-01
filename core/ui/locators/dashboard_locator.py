"""
DashboardLocator — Element selectors for the Dashboard page.

Design principles:
  - Class-based string constants (consistent with LoginLocator and PIMLocator)
  - URL-based locators preferred over text-based (language-agnostic)
  - All selectors verified against OrangeHRM OS 5.9
"""


class DashboardLocator:
    """
    Static CSS / XPath selectors for the Dashboard page.

    Uses class-level string constants (same pattern as LoginLocator and
    PIMLocator) so selectors can be passed directly to BasePage methods
    without instantiating this class.
    """

    # ── Dashboard Header ──────────────────────────────────────────────────────
    # URL-based — language-agnostic (works regardless of OrangeHRM locale)
    DASHBOARD_TITLE  = "//a[@href='/web/index.php/dashboard/index']"

    # Text-based fallback — English only, use only when URL-based is unavailable
    DASHBOARD_HEADER = "//h6[text()='Dashboard']"

    # ── Dashboard Widgets ─────────────────────────────────────────────────────
    TIME_AT_WORK     = "//p[text()='Time at Work']"
    MY_ACTIONS       = "//p[text()='My Actions']"
    QUICK_LAUNCH     = "//p[text()='Quick Launch']"
    BUZZ_LATEST_POST = "//p[text()='Buzz Latest Posts']"

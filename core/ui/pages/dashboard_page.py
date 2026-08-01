"""
DashboardPage — Page Object for the Dashboard page.

Extends BasePage for all Playwright interactions.
Covers: dashboard verification, left-menu navigation.
"""

from playwright.sync_api import expect

from core.ui.pages.base_page import BasePage
from core.ui.locators.dashboard_locator import DashboardLocator
from core.ui.components.left_menu import LeftMenu


class DashboardPage(BasePage):
    """
    Page Object for the OrangeHRM Dashboard page.

    Extends BasePage so self.page is always available for Playwright
    interactions via the inherited helper methods.
    """

    def __init__(self, page) -> None:
        super().__init__(page)          # sets self.page via BasePage
        self.left_menu = LeftMenu(page)

    # ── Dashboard Verification ────────────────────────────────────────────────

    def verify_dashboard(self) -> bool:
        """
        Assert the Dashboard navigation link is visible.

        Uses Playwright's expect() for built-in retry logic.
        Returns True on success; raises PlaywrightAssertionError on failure.

        Returns
        -------
        bool — True if dashboard is visible
        """
        expect(
            self.page.locator(DashboardLocator.DASHBOARD_TITLE)
        ).to_be_visible(timeout=10_000)
        return True

    def is_dashboard_visible(self) -> bool:
        """
        Return True if the Dashboard navigation link is currently visible.
        Does NOT raise — safe to use in conditional checks.
        """
        return self.is_visible(DashboardLocator.DASHBOARD_TITLE)

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to_admin(self) -> None:
        """Click Admin in the left navigation menu."""
        self.left_menu.click_admin()

    def navigate_to_pim(self) -> None:
        """Click PIM in the left navigation menu."""
        self.left_menu.click_pim()

    def navigate_to_leave(self) -> None:
        """Click Leave in the left navigation menu."""
        self.left_menu.click_leave()

    def navigate_to_time(self) -> None:
        """Click Time in the left navigation menu."""
        self.left_menu.click_time()

    def navigate_to_recruitment(self) -> None:
        """Click Recruitment in the left navigation menu."""
        self.left_menu.click_recruitment()

    def navigate_to_my_info(self) -> None:
        """Click My Info in the left navigation menu."""
        self.left_menu.click_my_info()

    def navigate_to_performance(self) -> None:
        """Click Performance in the left navigation menu."""
        self.left_menu.click_performance()

    def navigate_to_directory(self) -> None:
        """Click Directory in the left navigation menu."""
        self.left_menu.click_directory()

    def navigate_to_maintenance(self) -> None:
        """Click Maintenance in the left navigation menu."""
        self.left_menu.click_maintenance()

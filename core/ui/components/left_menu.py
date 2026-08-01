"""
LeftMenu — Component wrapper for the left navigation menu.

Provides named click methods for every menu item.
Uses LeftMenuLocator (URL-based, language-agnostic selectors).
"""

from core.ui.components.left_menu_locator import LeftMenuLocator


class LeftMenu:
    """Component wrapper for the OrangeHRM left navigation menu."""

    def __init__(self, page) -> None:
        self.menu = LeftMenuLocator(page)

    # ── Menu Item Click Methods ───────────────────────────────────────────────

    def click_admin(self) -> None:
        """Click the Admin menu item."""
        self.menu.admin.click()

    def click_pim(self) -> None:
        """Click the PIM menu item."""
        self.menu.pim.click()

    def click_leave(self) -> None:
        """Click the Leave menu item."""
        self.menu.leave.click()

    def click_time(self) -> None:
        """Click the Time menu item."""
        self.menu.time.click()

    def click_recruitment(self) -> None:
        """Click the Recruitment menu item."""
        self.menu.recruitment.click()

    def click_my_info(self) -> None:
        """Click the My Info menu item."""
        self.menu.my_info.click()

    def click_performance(self) -> None:
        """Click the Performance menu item."""
        self.menu.performance.click()

    def click_dashboard(self) -> None:
        """Click the Dashboard menu item."""
        self.menu.dashboard.click()

    def click_directory(self) -> None:
        """Click the Directory menu item."""
        self.menu.directory.click()

    def click_maintenance(self) -> None:
        """Click the Maintenance menu item."""
        self.menu.maintenance.click()

    def click_claim(self) -> None:
        """Click the Claim menu item."""
        self.menu.claim.click()

    def click_buzz(self) -> None:
        """Click the Buzz menu item."""
        self.menu.buzz.click()

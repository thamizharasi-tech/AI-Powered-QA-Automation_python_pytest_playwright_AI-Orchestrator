"""
Leave Page Objects
==================
Page Objects for the Leave module (Apply for Leave + My Leave).

Follows the framework pattern:
  - Locators in core/ui/locators/leave_locator.py
  - Page Objects here extend BasePage
  - Tests in tests/ui/test_leave_management.py

Usage:
    from core.ui.pages.leave_page import LeaveApplyPage, MyLeavePage
    from core.ui.pages.dashboard_page import DashboardPage

    leave_page = LeaveApplyPage(page)
    leave_page.navigate_to_apply_leave()
    leave_page.apply_leave("Annual Leave", "2025-08-01", "2025-08-02")
    assert leave_page.is_success_shown()
"""

from core.ui.pages.base_page import BasePage
from core.ui.pages.dashboard_page import DashboardPage
from core.ui.locators.leave_locator import LeaveApplyLocator, MyLeaveLocator


class LeaveApplyPage(BasePage):
    """
    Page Object for the Leave > Apply page.

    Responsibilities:
      - Navigate to Leave > Apply
      - Fill and submit the leave application form
      - Verify success/error/validation feedback
    """

    def navigate_to_apply_leave(self) -> None:
        """
        Navigate to Leave > Apply page via the left menu.

        OrangeHRM uses Vue.js with an oxd-form-loader overlay that intercepts
        pointer events while the form is loading. This method waits aggressively
        for the overlay to fully disappear before returning, so that subsequent
        interactions (select_leave_type, enter_from_date, etc.) do not fail.
        """
        dashboard = DashboardPage(self.page)
        dashboard.navigate_to_leave()
        self.wait_for_element(LeaveApplyLocator.APPLY_SUBMENU)
        self.click(LeaveApplyLocator.APPLY_SUBMENU)

        # 1. Wait for DOM content to load after navigation
        self.page.wait_for_load_state("domcontentloaded")

        # 2. Aggressively wait for the oxd-form-loader overlay to disappear.
        #    The loader intercepts ALL pointer events while visible.
        #    Retry up to 60s — on slow machines the loader can persist longer.
        for attempt in range(3):
            try:
                self.page.locator("div.oxd-form-loader").wait_for(
                    state="hidden", timeout=60_000
                )
                break  # Loader gone — proceed
            except Exception:
                # Loader may not appear at all on fast connections — safe to continue
                break

        # 3. Extra stabilisation wait — Vue re-renders the form after loader hides.
        #    Without this, the dropdown element exists in DOM but is not yet
        #    interactive (still being re-attached by Vue's virtual DOM diffing).
        self.page.wait_for_timeout(3000)

        # 4. Wait for the Leave Type dropdown to be visible AND stable.
        #    Use a polling loop: wait for visible, then confirm loader is gone.
        for attempt in range(3):
            try:
                self.page.wait_for_selector(
                    ".oxd-select-text-input",
                    state="visible",
                    timeout=30_000,
                )
                # Double-check loader is still gone after dropdown appears
                loader = self.page.locator("div.oxd-form-loader")
                if loader.is_visible(timeout=1_000):
                    # Loader reappeared — wait again
                    self.page.locator("div.oxd-form-loader").wait_for(
                        state="hidden", timeout=30_000
                    )
                    self.page.wait_for_timeout(2000)
                else:
                    break  # Dropdown visible and loader gone — ready
            except Exception:
                if attempt == 2:
                    raise  # Re-raise on final attempt
                self.page.wait_for_timeout(2000)

    def select_leave_type(self, leave_type: str) -> None:
        """
        Select a leave type from the dropdown.

        Parameters
        ----------
        leave_type : str — visible text of the leave type option
        """
        self.wait_for_element(LeaveApplyLocator.LEAVE_TYPE_DROPDOWN)
        self.click(LeaveApplyLocator.LEAVE_TYPE_DROPDOWN)
        option_locator = LeaveApplyLocator.LEAVE_TYPE_OPTION.format(leave_type)
        self.wait_for_element(option_locator)
        if not self.is_visible(option_locator):
            raise ValueError(f"Leave type '{leave_type}' not found in dropdown")
        self.click(option_locator)

    def enter_from_date(self, date_value: str) -> None:
        """Enter the From Date field. Format: YYYY-MM-DD"""
        self.wait_for_element(LeaveApplyLocator.FROM_DATE_INPUT)
        self.fill(LeaveApplyLocator.FROM_DATE_INPUT, date_value)

    def enter_to_date(self, date_value: str) -> None:
        """Enter the To Date field. Format: YYYY-MM-DD"""
        self.wait_for_element(LeaveApplyLocator.TO_DATE_INPUT)
        self.fill(LeaveApplyLocator.TO_DATE_INPUT, date_value)

    def enter_comments(self, comments: str) -> None:
        """Enter optional comments (max 250 chars)."""
        self.wait_for_element(LeaveApplyLocator.COMMENTS_TEXTAREA)
        self.fill(LeaveApplyLocator.COMMENTS_TEXTAREA, comments)

    def click_apply(self) -> None:
        """Click the Apply submit button."""
        self.wait_for_element(LeaveApplyLocator.APPLY_BUTTON)
        self.click(LeaveApplyLocator.APPLY_BUTTON)

    def apply_leave(
        self,
        leave_type: str,
        from_date: str,
        to_date: str,
        comments: str = "",
    ) -> None:
        """
        Fill and submit the leave application form.

        Parameters
        ----------
        leave_type : str — leave type visible text
        from_date  : str — YYYY-MM-DD
        to_date    : str — YYYY-MM-DD
        comments   : str — optional comment text
        """
        self.select_leave_type(leave_type)
        self.enter_from_date(from_date)
        self.enter_to_date(to_date)
        if comments:
            self.enter_comments(comments)
        self.click_apply()

    def is_success_shown(self) -> bool:
        """Return True if the success toast is visible."""
        return self.is_visible(LeaveApplyLocator.SUCCESS_MESSAGE)

    def is_error_shown(self) -> bool:
        """Return True if the error toast is visible."""
        return self.is_visible(LeaveApplyLocator.ERROR_MESSAGE)

    def is_validation_error_shown(self) -> bool:
        """Return True if an inline validation error is visible."""
        return self.is_visible(LeaveApplyLocator.VALIDATION_ERROR)

    def get_error_text(self) -> str:
        """Return the text of the error toast message."""
        self.wait_for_element(LeaveApplyLocator.ERROR_MESSAGE)
        return self.get_text(LeaveApplyLocator.ERROR_MESSAGE)

    def get_validation_error_text(self) -> str:
        """Return the text of the inline validation error."""
        self.wait_for_element(LeaveApplyLocator.VALIDATION_ERROR)
        return self.get_text(LeaveApplyLocator.VALIDATION_ERROR)

    def get_balance_text(self) -> str:
        """Return the leave balance display text, or empty string if not visible."""
        if self.is_visible(LeaveApplyLocator.BALANCE_DISPLAY):
            return self.get_text(LeaveApplyLocator.BALANCE_DISPLAY)
        return ""


class MyLeavePage(BasePage):
    """
    Page Object for the My Leave list page.

    Responsibilities:
      - Navigate to My Leave
      - Verify leave requests exist in the list
      - Read leave request status
    """

    def navigate_to_my_leave(self) -> None:
        """Navigate to the My Leave page."""
        self.wait_for_element(MyLeaveLocator.MY_LEAVE_MENU)
        self.click(MyLeaveLocator.MY_LEAVE_MENU)
        self.wait_for_element(MyLeaveLocator.LEAVE_LIST_TABLE)

    def find_leave_request(
        self,
        leave_type: str,
        from_date: str,
        to_date: str,
    ) -> bool:
        """
        Return True if a matching leave request exists in the list.

        Parameters
        ----------
        leave_type : str — leave type text to match
        from_date  : str — from date text to match
        to_date    : str — to date text to match
        """
        self.wait_for_element(MyLeaveLocator.LEAVE_LIST_TABLE)
        row_count = self.page.locator(MyLeaveLocator.LEAVE_ROW).count()
        for i in range(row_count):
            row = f"({MyLeaveLocator.LEAVE_ROW})[{i + 1}]"
            row_type  = self.get_text(f"{row}{MyLeaveLocator.LEAVE_TYPE_CELL}")
            row_from  = self.get_text(f"{row}{MyLeaveLocator.FROM_DATE_CELL}")
            row_to    = self.get_text(f"{row}{MyLeaveLocator.TO_DATE_CELL}")
            if leave_type in row_type and from_date in row_from and to_date in row_to:
                return True
        return False

    def get_leave_status(self, leave_type: str, from_date: str) -> str:
        """
        Return the status of a leave request, or empty string if not found.

        Parameters
        ----------
        leave_type : str — leave type text to match
        from_date  : str — from date text to match
        """
        self.wait_for_element(MyLeaveLocator.LEAVE_LIST_TABLE)
        row_count = self.page.locator(MyLeaveLocator.LEAVE_ROW).count()
        for i in range(row_count):
            row = f"({MyLeaveLocator.LEAVE_ROW})[{i + 1}]"
            row_type = self.get_text(f"{row}{MyLeaveLocator.LEAVE_TYPE_CELL}")
            row_from = self.get_text(f"{row}{MyLeaveLocator.FROM_DATE_CELL}")
            if leave_type in row_type and from_date in row_from:
                return self.get_text(f"{row}{MyLeaveLocator.STATUS_CELL}")
        return ""

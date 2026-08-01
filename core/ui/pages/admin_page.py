"""
AdminPage — Page Object for the Admin → User Management module.

Extends BasePage for all Playwright interactions.

Covers:
  - Navigate to Admin → User Management → Users
  - Add System User form (User Role dropdown, Status dropdown,
    Employee Name autocomplete, Username, Password)
  - Search users by username
  - Verify user in list / no records found

Playwright Concepts Demonstrated:
  - Dropdowns via oxd-select-text-input (User Role, Status)
  - Autocomplete/typeahead (Employee Name)
  - web-first assertions via expect()
  - .first locator to avoid strict mode violations

Framework components:
  - BasePage (core/ui/pages/base_page.py)
  - AdminLocator (core/ui/locators/admin_locator.py)
  - LeftMenu (core/ui/components/left_menu.py)
  - Playwright expect API
"""

from playwright.sync_api import expect

from core.ui.pages.base_page import BasePage
from core.ui.locators.admin_locator import AdminLocator
from core.ui.components.left_menu import LeftMenu


class AdminPage(BasePage):
    """Page Object for the Admin → User Management module."""

    def __init__(self, page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to_admin(self) -> None:
        """Click Admin in the left navigation menu and wait for page load."""
        LeftMenu(self.page).click_admin()
        self.page.wait_for_load_state("domcontentloaded")

    def navigate_to_user_management(self) -> None:
        """
        Navigate to Admin → User Management → Users.

        Clicks the Admin menu, then the User Management submenu,
        then the Users link. Waits for the System Users page to load.
        """
        self.navigate_to_admin()
        # User Management is a submenu — click it to expand
        self.wait_for_element(AdminLocator.USER_MANAGEMENT_MENU)
        self.click(AdminLocator.USER_MANAGEMENT_MENU)
        # Click the Users link in the expanded submenu
        self.wait_for_element(AdminLocator.USERS_SUBMENU)
        self.click(AdminLocator.USERS_SUBMENU)
        self.page.wait_for_load_state("domcontentloaded")

    def verify_system_users_page(self) -> None:
        """Assert the System Users page title is visible."""
        expect(
            self.page.locator(AdminLocator.SYSTEM_USERS_TITLE)
        ).to_be_visible(timeout=10_000)

    # ── Add User Form ─────────────────────────────────────────────────────────

    def click_add_user(self) -> None:
        """Click the Add button to open the Add User form."""
        self.click(AdminLocator.ADD_USER_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def select_user_role(self, role: str) -> None:
        """
        Select a User Role from the dropdown.

        Parameters
        ----------
        role : str — 'Admin' or 'ESS'
        """
        self.wait_for_element(AdminLocator.USER_ROLE_DROPDOWN)
        self.click(AdminLocator.USER_ROLE_DROPDOWN)
        option = AdminLocator.USER_ROLE_OPTION.format(role)
        self.wait_for_element(option)
        self.click(option)

    def select_status(self, status: str) -> None:
        """
        Select a Status from the dropdown.

        Parameters
        ----------
        status : str — 'Enabled' or 'Disabled'
        """
        self.wait_for_element(AdminLocator.STATUS_DROPDOWN)
        self.click(AdminLocator.STATUS_DROPDOWN)
        option = AdminLocator.STATUS_OPTION.format(status)
        self.wait_for_element(option)
        self.click(option)

    def enter_employee_name(self, employee_name: str) -> None:
        """
        Type an employee name in the autocomplete field and select the first suggestion.

        Uses type() with delay to trigger the autocomplete dropdown.
        Waits up to 10s for the suggestion to appear, then clicks it.
        Raises ValueError if no suggestion appears (employee not found).

        Parameters
        ----------
        employee_name : str — partial or full employee name to search
        """
        name_input = self.page.locator(AdminLocator.EMPLOYEE_NAME_INPUT)
        name_input.wait_for(state="visible", timeout=10_000)
        name_input.click()
        # Clear any existing value first
        name_input.fill("")
        name_input.type(employee_name, delay=80)

        # Wait for autocomplete dropdown and click first suggestion
        # The dropdown must be clicked for the form to accept the employee
        suggestion = self.page.locator(AdminLocator.AUTOCOMPLETE_OPTION).first
        suggestion.wait_for(state="visible", timeout=10_000)
        suggestion.click()
        # Wait for the field to be populated with the selected employee
        self.page.wait_for_timeout(500)

    def enter_username(self, username: str) -> None:
        """Fill the Username field on the Add User form."""
        self.fill(AdminLocator.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        """Fill the Password field on the Add User form."""
        self.fill(AdminLocator.PASSWORD_INPUT, password)

    def enter_confirm_password(self, confirm_password: str) -> None:
        """Fill the Confirm Password field on the Add User form."""
        self.fill(AdminLocator.CONFIRM_PASSWORD_INPUT, confirm_password)

    def click_save(self) -> None:
        """Click the Save button on the Add User form."""
        self.click(AdminLocator.SAVE_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def click_cancel(self) -> None:
        """Click the Cancel button on the Add User form."""
        self.click(AdminLocator.CANCEL_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def add_user(
        self,
        role: str,
        status: str,
        employee_name: str,
        username: str,
        password: str,
        confirm_password: str,
    ) -> None:
        """
        Fill and submit the Add User form.

        Parameters
        ----------
        role             : str — 'Admin' or 'ESS'
        status           : str — 'Enabled' or 'Disabled'
        employee_name    : str — employee name for autocomplete
        username         : str — system login username
        password         : str — password
        confirm_password : str — must match password
        """
        self.select_user_role(role)
        self.enter_employee_name(employee_name)
        self.select_status(status)
        self.enter_username(username)
        self.enter_password(password)
        self.enter_confirm_password(confirm_password)
        self.click_save()

    # ── Search ────────────────────────────────────────────────────────────────

    def search_user_by_username(self, username: str) -> None:
        """
        Search for a system user by username.

        Parameters
        ----------
        username : str — username to search for
        """
        self.fill(AdminLocator.SEARCH_USERNAME_INPUT, username)
        self.click(AdminLocator.SEARCH_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def reset_search(self) -> None:
        """Click the Reset button to clear search filters."""
        self.click(AdminLocator.RESET_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    # ── Assertions ────────────────────────────────────────────────────────────

    def verify_user_in_list(self) -> None:
        """Assert that at least one user row is visible in the results table."""
        expect(
            self.page.locator(AdminLocator.USER_TABLE_ROWS).first
        ).to_be_visible(timeout=10_000)

    def verify_no_records_found(self) -> None:
        """Assert that the 'No Records Found' message is visible."""
        expect(
            self.page.locator(AdminLocator.NO_RECORDS_FOUND)
        ).to_be_visible(timeout=10_000)

    def verify_add_success(self) -> None:
        """Assert the success toast is visible after adding a user."""
        expect(
            self.page.locator(AdminLocator.SUCCESS_TOAST)
        ).to_be_visible(timeout=10_000)

    def verify_required_error(self) -> None:
        """Assert that at least one 'Required' validation error is visible."""
        expect(
            self.page.locator(AdminLocator.REQUIRED_ERROR).first
        ).to_be_visible(timeout=5_000)

    def get_user_row_count(self) -> int:
        """Return the number of user rows currently visible in the table."""
        self.page.wait_for_load_state("domcontentloaded")
        return self.page.locator(AdminLocator.USER_TABLE_ROWS).count()

    def is_user_in_list(self) -> bool:
        """Return True if at least one user row is visible."""
        return self.page.locator(AdminLocator.USER_TABLE_ROWS).count() > 0

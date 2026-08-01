"""
PIMPage — Page Object for the PIM (Personnel Information Management) module.

Extends BasePage for all Playwright interactions.

Covers:
  - Navigate to PIM module
  - Employee List page
  - Add Employee form (mandatory fields, optional fields, login credentials)
  - Personal Details page (post-save verification)
  - Employee search / verification in Employee List

Framework components:
  - BasePage (core/ui/pages/base_page.py)
  - PIMLocator (core/ui/locators/pim_locator.py)
  - LeftMenu (core/ui/components/left_menu.py)
  - Playwright expect API
"""

from playwright.sync_api import expect

from core.ui.pages.base_page import BasePage
from core.ui.locators.pim_locator import PIMLocator
from core.ui.components.left_menu import LeftMenu


class PIMPage(BasePage):
    """Page Object for the PIM module — Add Employee and Employee List flows."""

    def __init__(self, page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to_pim(self) -> None:
        """Click PIM in the left navigation menu and wait for page load."""
        LeftMenu(self.page).click_pim()
        self.page.wait_for_load_state("domcontentloaded")

    def verify_pim_page(self) -> None:
        """Assert the PIM module header is visible."""
        expect(self.page.locator(PIMLocator.PIM_HEADER)).to_be_visible(timeout=10_000)

    def verify_pim_header(self) -> None:
        """Alias for verify_pim_page()."""
        self.verify_pim_page()

    def verify_employee_list_page(self) -> None:
        """Assert the Employee List page title is visible."""
        expect(
            self.page.locator(PIMLocator.EMPLOYEE_LIST_TITLE)
        ).to_be_visible(timeout=10_000)

    def verify_employee_list_title(self) -> None:
        """Alias for verify_employee_list_page()."""
        self.verify_employee_list_page()

    # ── Add Employee Form ─────────────────────────────────────────────────────

    def click_add_employee(self) -> None:
        """Click the 'Add' button on the Employee List page."""
        self.click(PIMLocator.ADD_EMPLOYEE_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def verify_add_employee_form(self) -> None:
        """Assert the Add Employee form title is visible."""
        expect(
            self.page.locator(PIMLocator.ADD_EMPLOYEE_TITLE)
        ).to_be_visible(timeout=10_000)

    def verify_add_employee_title(self) -> None:
        """Alias for verify_add_employee_form()."""
        self.verify_add_employee_form()

    def enter_first_name(self, first_name: str) -> None:
        """Fill the First Name field."""
        self.fill(PIMLocator.FIRST_NAME_INPUT, first_name)

    def enter_middle_name(self, middle_name: str) -> None:
        """Fill the Middle Name field (optional)."""
        self.fill(PIMLocator.MIDDLE_NAME_INPUT, middle_name)

    def enter_last_name(self, last_name: str) -> None:
        """Fill the Last Name field."""
        self.fill(PIMLocator.LAST_NAME_INPUT, last_name)

    def get_employee_id(self) -> str:
        """
        Read the Employee ID field value.

        Branches on the current URL:
          - viewPersonalDetails → Personal Details page after save:
            waits for the field to have a non-empty value using
            Playwright's expect() (no time.sleep).
          - Otherwise → still on Add Employee form:
            reads the Employee ID input directly.

        Returns
        -------
        str — the Employee ID value, or "" if not found
        """
        current_url = self.page.url

        if "viewPersonalDetails" in current_url:
            self.page.wait_for_load_state("domcontentloaded")
            locator = self.page.locator(PIMLocator.EMPLOYEE_ID_DISPLAY)
            locator.wait_for(state="visible", timeout=10_000)
            # Use Playwright's built-in retry — no time.sleep()
            expect(locator).not_to_have_value("", timeout=10_000)
            return locator.input_value()
        else:
            locator = self.page.locator(PIMLocator.EMPLOYEE_ID_INPUT)
            locator.wait_for(state="visible", timeout=10_000)
            return locator.input_value()

    def set_employee_id(self, employee_id: str) -> None:
        """Override the Employee ID field with a custom value."""
        locator = self.page.locator(PIMLocator.EMPLOYEE_ID_INPUT)
        locator.wait_for(state="visible", timeout=10_000)
        locator.click(click_count=3)   # select-all via triple-click
        locator.fill(employee_id)

    def clear_and_enter_employee_id(self, employee_id: str) -> None:
        """Clear the auto-generated Employee ID and enter a custom one."""
        emp_id_locator = self.page.locator(PIMLocator.EMPLOYEE_ID_INPUT)
        emp_id_locator.wait_for(state="visible", timeout=10_000)
        emp_id_locator.clear()
        emp_id_locator.fill(employee_id)

    def enter_employee_id(self, employee_id: str) -> None:
        """Alias for clear_and_enter_employee_id()."""
        self.clear_and_enter_employee_id(employee_id)

    def enable_create_login(self) -> None:
        """Toggle the 'Create Login Details' switch ON."""
        self.click(PIMLocator.CREATE_LOGIN_TOGGLE)

    def enter_login_username(self, username: str) -> None:
        """Fill the Username field in the login details section."""
        self.fill(PIMLocator.USERNAME_INPUT, username)

    def enter_username(self, username: str) -> None:
        """Alias for enter_login_username()."""
        self.enter_login_username(username)

    def enter_login_password(self, password: str) -> None:
        """Fill the Password field in the login details section."""
        self.fill(PIMLocator.PASSWORD_INPUT, password)

    def enter_password(self, password: str) -> None:
        """Alias for enter_login_password()."""
        self.enter_login_password(password)

    def enter_confirm_password(self, confirm_password: str) -> None:
        """Fill the Confirm Password field in the login details section."""
        self.fill(PIMLocator.CONFIRM_PASSWORD_INPUT, confirm_password)

    def click_save(self) -> None:
        """Click the Save button on the Add Employee form."""
        self.click(PIMLocator.SAVE_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def click_cancel(self) -> None:
        """Click the Cancel button on the Add Employee form."""
        self.click(PIMLocator.CANCEL_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def fill_add_employee_form(
        self,
        first_name: str,
        last_name: str,
        middle_name: str = "",
        employee_id: str = "",
    ) -> None:
        """
        Fill the Add Employee form with the provided details.

        Parameters
        ----------
        first_name   : str — mandatory
        last_name    : str — mandatory
        middle_name  : str — optional
        employee_id  : str — optional; if provided, replaces the auto-generated ID
        """
        self.enter_first_name(first_name)
        if middle_name:
            self.enter_middle_name(middle_name)
        self.enter_last_name(last_name)
        if employee_id:
            self.clear_and_enter_employee_id(employee_id)

    def add_employee(
        self,
        first_name: str,
        last_name: str,
        middle_name: str = "",
        employee_id: str = "",
    ) -> None:
        """Fill and submit the Add Employee form with mandatory fields only."""
        self.fill_add_employee_form(first_name, last_name, middle_name, employee_id)
        self.click_save()

    def add_employee_with_login(
        self,
        first_name: str,
        last_name: str,
        username: str,
        password: str,
        confirm_password: str,
        middle_name: str = "",
        employee_id: str = "",
    ) -> None:
        """Fill and submit the Add Employee form including login credentials."""
        self.enter_first_name(first_name)
        if middle_name:
            self.enter_middle_name(middle_name)
        self.enter_last_name(last_name)
        if employee_id:
            self.clear_and_enter_employee_id(employee_id)
        self.enable_create_login()
        self.enter_login_username(username)
        self.enter_login_password(password)
        self.enter_confirm_password(confirm_password)
        self.click_save()

    # ── Post-Save Verification ────────────────────────────────────────────────

    def verify_personal_details_page(self) -> None:
        """
        Assert the Personal Details page is displayed after saving.

        After saving Add Employee, OrangeHRM redirects to:
          /pim/viewPersonalDetails/empNumber/<id>
        Waits for the URL to contain 'viewPersonalDetails' as the
        reliable indicator that the employee was created successfully.
        Timeout is 30s to handle slow demo server responses.
        """
        self.page.wait_for_url("**/viewPersonalDetails/**", timeout=30_000)

    def get_employee_id_from_personal_details(self) -> str:
        """
        Read the Employee ID from the Personal Details page after save.

        Waits for the URL to contain 'viewPersonalDetails' first, then
        reads the Employee ID input field value.
        """
        self.page.wait_for_url("**/viewPersonalDetails/**", timeout=15_000)
        self.page.wait_for_load_state("domcontentloaded")
        emp_id_locator = self.page.locator(PIMLocator.EMPLOYEE_ID_DISPLAY)
        emp_id_locator.wait_for(state="visible", timeout=10_000)
        return emp_id_locator.input_value()

    def get_saved_employee_id(self) -> str:
        """Alias for get_employee_id_from_personal_details()."""
        return self.get_employee_id_from_personal_details()

    def verify_success_toast(self) -> None:
        """Assert the success toast notification is visible."""
        expect(
            self.page.locator(PIMLocator.SUCCESS_TOAST)
        ).to_be_visible(timeout=10_000)

    # ── Validation / Error Assertions ─────────────────────────────────────────

    def verify_required_field_error(self) -> None:
        """Assert that at least one 'Required' validation error is visible."""
        expect(
            self.page.locator(PIMLocator.REQUIRED_FIELD_ERROR).first
        ).to_be_visible(timeout=5_000)

    def verify_first_name_required_error(self) -> None:
        """Assert that the 'Required' validation error for First Name is visible."""
        expect(
            self.page.locator(PIMLocator.FIRST_NAME_REQUIRED)
        ).to_be_visible(timeout=5_000)

    def verify_last_name_required_error(self) -> None:
        """Assert that the 'Required' validation error for Last Name is visible."""
        expect(
            self.page.locator(PIMLocator.LAST_NAME_REQUIRED)
        ).to_be_visible(timeout=5_000)

    def verify_already_exists_error(self) -> None:
        """Assert that the 'Already exists' error is visible."""
        expect(
            self.page.locator(PIMLocator.ALREADY_EXISTS_ERROR)
        ).to_be_visible(timeout=5_000)

    def verify_password_mismatch_error(self) -> None:
        """Assert that the 'Passwords do not match' error is visible."""
        expect(
            self.page.locator(PIMLocator.PASSWORD_MISMATCH_ERROR)
        ).to_be_visible(timeout=5_000)

    def is_required_error_visible(self) -> bool:
        """Return True if any 'Required' validation error is visible."""
        return self.page.locator(PIMLocator.REQUIRED_FIELD_ERROR).first.is_visible()

    def is_already_exists_error_visible(self) -> bool:
        """Return True if the 'Already exists' error is visible."""
        return self.page.locator(PIMLocator.ALREADY_EXISTS_ERROR).is_visible()

    def is_password_mismatch_error_visible(self) -> bool:
        """Return True if the 'Passwords do not match' error is visible."""
        return self.page.locator(PIMLocator.PASSWORD_MISMATCH_ERROR).is_visible()

    def is_first_name_required_visible(self) -> bool:
        """Return True if the First Name 'Required' error is visible."""
        return self.page.locator(PIMLocator.FIRST_NAME_REQUIRED).is_visible()

    def is_last_name_required_visible(self) -> bool:
        """Return True if the Last Name 'Required' error is visible."""
        return self.page.locator(PIMLocator.LAST_NAME_REQUIRED).is_visible()

    def is_employee_list_page(self) -> bool:
        """Return True if the Employee List title is currently visible."""
        return self.page.locator(PIMLocator.EMPLOYEE_LIST_TITLE).is_visible()

    # ── Employee List / Search ────────────────────────────────────────────────

    def search_employee_by_name(self, employee_name: str) -> None:
        """
        Search for an employee by name in the Employee List.

        The Employee Name field is a typeahead autocomplete — types
        character-by-character to trigger the dropdown, then selects
        the first matching suggestion. If no suggestion appears (e.g.
        non-existent name), proceeds directly to clicking Search.
        """
        name_input = self.page.locator(PIMLocator.EMPLOYEE_NAME_SEARCH)
        name_input.click()
        name_input.type(employee_name, delay=50)

        # Wait for autocomplete dropdown and click first suggestion
        try:
            suggestion = self.page.locator(
                "//div[contains(@class,'oxd-autocomplete-option')]"
            ).first
            suggestion.wait_for(state="visible", timeout=8_000)
            suggestion.click()
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            # No autocomplete suggestion — name may not exist in system
            pass

        self.click(PIMLocator.SEARCH_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def search_employee_by_id(self, employee_id: str) -> None:
        """Search for an employee by ID in the Employee List."""
        self.fill(PIMLocator.EMPLOYEE_ID_SEARCH, employee_id)
        self.click(PIMLocator.SEARCH_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    def verify_employee_in_list(self) -> None:
        """Assert that at least one employee row is visible in the results table."""
        expect(
            self.page.locator(PIMLocator.EMPLOYEE_TABLE_ROWS).first
        ).to_be_visible(timeout=10_000)

    def verify_no_records_found(self) -> None:
        """Assert that the 'No Records Found' message is visible."""
        expect(
            self.page.locator(PIMLocator.NO_RECORDS_FOUND)
        ).to_be_visible(timeout=10_000)

    def get_employee_row_count(self) -> int:
        """Return the number of employee rows currently visible in the table."""
        self.page.wait_for_load_state("domcontentloaded")
        return self.page.locator(PIMLocator.EMPLOYEE_TABLE_ROWS).count()

    def is_employee_in_list(self) -> bool:
        """Return True if at least one employee row is visible in the results table."""
        return self.page.locator(PIMLocator.EMPLOYEE_TABLE_ROWS).count() > 0

    def is_no_records_found(self) -> bool:
        """Return True if the 'No Records Found' message is visible."""
        return self.page.locator(PIMLocator.NO_RECORDS_FOUND).is_visible()

    def click_reset_search(self) -> None:
        """Click the Reset button to clear the search filters."""
        self.click(PIMLocator.RESET_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")

    # ── Edit Employee ─────────────────────────────────────────────────────────

    def click_edit_first_result(self) -> None:
        """
        Click the Edit (pencil) button on the first row of the employee table.

        Uses .first to avoid Playwright strict mode violation when multiple
        rows are present. Waits for the Personal Details URL after clicking.
        """
        # Use .first to target only the first row's first button (Edit icon)
        edit_btn = self.page.locator(
            "//div[@class='oxd-table-body']//div[@role='row']//button[1]"
        ).first
        edit_btn.wait_for(state="visible", timeout=10_000)
        edit_btn.scroll_into_view_if_needed()
        edit_btn.click()
        self.page.wait_for_url("**/viewPersonalDetails/**", timeout=15_000)
        self.page.wait_for_load_state("domcontentloaded")

    def update_first_name(self, new_first_name: str) -> None:
        """
        Update the First Name field on the Personal Details page.

        OrangeHRM's Personal Details page renders name fields as editable
        inputs directly — no separate edit icon needed for the name section.
        Clears the existing value and fills with the new one.
        """
        locator = self.page.locator(PIMLocator.PERSONAL_DETAILS_FIRST_NAME)
        locator.wait_for(state="visible", timeout=10_000)
        locator.click(click_count=3)   # select-all via triple-click
        locator.fill(new_first_name)

    def update_last_name(self, new_last_name: str) -> None:
        """
        Update the Last Name field on the Personal Details page.

        Clears the existing value and fills with the new one.
        """
        locator = self.page.locator(PIMLocator.PERSONAL_DETAILS_LAST_NAME)
        locator.wait_for(state="visible", timeout=10_000)
        locator.click(click_count=3)
        locator.fill(new_last_name)

    def save_personal_details(self) -> None:
        """
        Click the first Save button on the Personal Details page.

        The Personal Details page has multiple Save buttons (one per section).
        Using .first targets the name section Save button — the one relevant
        to first/last name edits. Waits for load state after clicking.
        """
        save_btn = self.page.locator(PIMLocator.PERSONAL_DETAILS_SAVE_BUTTON).first
        save_btn.wait_for(state="visible", timeout=10_000)
        save_btn.scroll_into_view_if_needed()
        save_btn.click()
        self.page.wait_for_load_state("domcontentloaded")

    def verify_update_success(self) -> None:
        """
        Assert the success toast is visible after saving Personal Details.

        Uses Playwright's web-first expect() for built-in retry logic —
        no explicit sleep or manual wait required.
        """
        expect(
            self.page.locator(PIMLocator.SUCCESS_TOAST)
        ).to_be_visible(timeout=10_000)

    def get_first_name_value(self) -> str:
        """Return the current value of the First Name field."""
        locator = self.page.locator(PIMLocator.PERSONAL_DETAILS_FIRST_NAME)
        locator.wait_for(state="visible", timeout=10_000)
        return locator.input_value()

    def get_last_name_value(self) -> str:
        """Return the current value of the Last Name field."""
        locator = self.page.locator(PIMLocator.PERSONAL_DETAILS_LAST_NAME)
        locator.wait_for(state="visible", timeout=10_000)
        return locator.input_value()

    # ── Delete Employee ───────────────────────────────────────────────────────

    def click_delete_first_result(self) -> None:
        """
        Click the Delete (trash) button on the first row of the employee table.

        Uses .first to avoid Playwright strict mode violation when multiple
        rows are present. The delete button is the second button in each row.
        After clicking, the confirmation modal appears.
        """
        delete_btn = self.page.locator(PIMLocator.DELETE_BUTTON_FIRST_ROW).first
        delete_btn.wait_for(state="visible", timeout=10_000)
        delete_btn.scroll_into_view_if_needed()
        delete_btn.click()

    def confirm_delete(self) -> None:
        """
        Click 'Yes, Delete' in the confirmation modal.

        OrangeHRM uses a custom modal dialog (not a browser alert).
        Waits for the modal to appear before clicking confirm.
        After confirming, waits for the page to reload.
        """
        confirm_btn = self.page.locator(PIMLocator.CONFIRM_DELETE_BUTTON)
        confirm_btn.wait_for(state="visible", timeout=10_000)
        confirm_btn.click()
        self.page.wait_for_load_state("domcontentloaded")

    def cancel_delete(self) -> None:
        """
        Click 'No, Cancel' in the confirmation modal.

        Dismisses the delete confirmation without deleting the employee.
        """
        cancel_btn = self.page.locator(PIMLocator.CANCEL_DELETE_BUTTON)
        cancel_btn.wait_for(state="visible", timeout=10_000)
        cancel_btn.click()
        self.page.wait_for_load_state("domcontentloaded")

    def verify_delete_modal_visible(self) -> None:
        """
        Assert the delete confirmation modal is visible.

        Uses web-first expect() for built-in retry logic.
        """
        expect(
            self.page.locator(PIMLocator.DELETE_CONFIRM_MODAL)
        ).to_be_visible(timeout=10_000)

    def verify_delete_success(self) -> None:
        """
        Assert the success toast is visible after deleting an employee.

        Uses web-first expect() for built-in retry logic.
        """
        expect(
            self.page.locator(PIMLocator.SUCCESS_TOAST)
        ).to_be_visible(timeout=10_000)

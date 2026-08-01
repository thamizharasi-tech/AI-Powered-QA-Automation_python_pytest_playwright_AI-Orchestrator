"""
test_edit_employee.py — Edit Employee Feature Tests
=====================================================
Feature   : PIM → Employee List → Edit Employee (OrangeHRM)
Story ID  : HRM-203

Business Value:
  HR Administrators update employee personal information regularly.
  This suite verifies that the Edit workflow navigates correctly,
  persists changes, and validates the updated data.

Playwright Concepts Demonstrated:
  - web-first assertions via expect() in PIMPage (verify_update_success,
    verify_employee_in_list, verify_required_field_error)
  - wait_for_url() for navigation confirmation after Edit click
  - .first locator to avoid strict mode violation on multi-row tables
  - triple-click (click_count=3) to select-all before fill
  - Auto-waiting on every interaction (BasePage)
  - Storage State session reuse (no repeated logins)

Framework Components Reused:
  - PIMPage          (core/ui/pages/pim_page.py)
  - SessionManager   (core/ui/session_manager.py)
  - result()         (core/common_modules.py)
  - read_api_data_from_excel / read_cloud_env (core/utils/XLUtils.py)
  - page fixture     (conftest.py)

Test Data:
  testData/API_testData.xlsx → sheet: Web_UI
  Row identifiers:
    TC_EditEmployee_UpdateName — new name values for edit tests

Test Cases:
  TC-EDIT-001  Edit employee first name — updated value persisted
  TC-EDIT-002  Edit employee last name  — updated value persisted
  TC-EDIT-003  Edit with empty first name — Required validation shown
  TC-EDIT-004  Navigate to edit page — Personal Details URL confirmed
"""

import allure
import pytest

from core.common_modules import result
from core.e2e_testData import url, username, password, storage_state_path
from core.ui.pages.pim_page import PIMPage
from core.ui.session_manager import SessionManager
from core.utils.XLUtils import read_api_data_from_excel, read_cloud_env


@allure.feature("Edit Employee")
class TestEditEmployee:
    """
    End-to-end test suite for PIM → Edit Employee (HRM-203).

    Pre-conditions:
      - At least one employee exists in OrangeHRM (demo data always has employees)
      - storageState.json exists (run test_generate_storage_state once)
    """

    # ── TC-EDIT-001: Update First Name ────────────────────────────────────────

    @allure.story("Update Employee Name")
    @allure.title("TC-EDIT-001: Edit employee first name — updated value persisted")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.ui
    def test_edit_employee_first_name(self, page):
        """
        Verify that editing an employee's first name saves successfully
        and the updated value is reflected on the Personal Details page.

        Steps:
          1. Login and navigate to PIM Employee List
          2. Click Edit on the first employee in the list
          3. Update the First Name field
          4. Save and verify success toast (web-first assertion)
          5. Verify the updated first name is displayed

        Test Data: testData/API_testData.xlsx → Web_UI → TC_EditEmployee_UpdateName
        """
        cloud_env = read_cloud_env()

        # ── Arrange: Load test data ───────────────────────────────────────────
        with allure.step("Arrange: Load test data from Excel"):
            try:
                data = read_api_data_from_excel("Web_UI", "TC_EditEmployee_UpdateName")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}
            new_first_name = str(data.get("NewFirstName", "EditedFirst"))

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM Employee List"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            try:
                pim_page.verify_employee_in_list()
                result("passed", "Employee List should have at least one row",
                       f"{pim_page.get_employee_row_count()} row(s) visible")
            except Exception as exc:
                result("failed", "Employee List should have at least one row", str(exc))
                raise

        with allure.step("Click Edit on the first employee"):
            try:
                pim_page.click_edit_first_result()
                result("passed", "Edit should navigate to Personal Details",
                       f"URL: {page.url}")
            except Exception as exc:
                result("failed", "Edit should navigate to Personal Details", str(exc))
                raise

        with allure.step(f"Update First Name to '{new_first_name}'"):
            try:
                pim_page.update_first_name(new_first_name)
                result("passed", f"First Name field should accept '{new_first_name}'",
                       "First Name updated")
            except Exception as exc:
                result("failed", f"First Name field should accept '{new_first_name}'", str(exc))
                raise

        with allure.step("Save Personal Details"):
            pim_page.save_personal_details()

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify success toast is displayed (web-first assertion)"):
            try:
                pim_page.verify_update_success()
                result("passed", "Success toast should be visible after save",
                       "Success toast is visible")
            except Exception as exc:
                result("failed", "Success toast should be visible after save", str(exc))
                raise

        with allure.step("Verify updated First Name is persisted"):
            try:
                actual = pim_page.get_first_name_value()
                assert actual == new_first_name, (
                    f"Expected First Name '{new_first_name}' but got '{actual}'"
                )
                result("passed",
                       f"First Name should be '{new_first_name}'",
                       f"First Name is '{actual}'")
            except AssertionError as exc:
                result("failed",
                       f"First Name should be '{new_first_name}'",
                       str(exc))
                raise

    # ── TC-EDIT-002: Update Last Name ─────────────────────────────────────────

    @allure.story("Update Employee Name")
    @allure.title("TC-EDIT-002: Edit employee last name — updated value persisted")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.ui
    def test_edit_employee_last_name(self, page):
        """
        Verify that editing an employee's last name saves successfully
        and the updated value is reflected on the Personal Details page.

        Test Data: testData/API_testData.xlsx → Web_UI → TC_EditEmployee_UpdateName
        """
        cloud_env = read_cloud_env()

        # ── Arrange: Load test data ───────────────────────────────────────────
        with allure.step("Arrange: Load test data from Excel"):
            try:
                data = read_api_data_from_excel("Web_UI", "TC_EditEmployee_UpdateName")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}
            new_last_name = str(data.get("NewLastName", "EditedLast"))

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM Employee List"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            try:
                pim_page.verify_employee_in_list()
                result("passed", "Employee List should have at least one row",
                       f"{pim_page.get_employee_row_count()} row(s) visible")
            except Exception as exc:
                result("failed", "Employee List should have at least one row", str(exc))
                raise

        with allure.step("Click Edit on the first employee"):
            try:
                pim_page.click_edit_first_result()
                result("passed", "Edit should navigate to Personal Details",
                       f"URL: {page.url}")
            except Exception as exc:
                result("failed", "Edit should navigate to Personal Details", str(exc))
                raise

        with allure.step(f"Update Last Name to '{new_last_name}'"):
            try:
                pim_page.update_last_name(new_last_name)
                result("passed", f"Last Name field should accept '{new_last_name}'",
                       "Last Name updated")
            except Exception as exc:
                result("failed", f"Last Name field should accept '{new_last_name}'", str(exc))
                raise

        with allure.step("Save Personal Details"):
            pim_page.save_personal_details()

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify success toast is displayed (web-first assertion)"):
            try:
                pim_page.verify_update_success()
                result("passed", "Success toast should be visible after save",
                       "Success toast is visible")
            except Exception as exc:
                result("failed", "Success toast should be visible after save", str(exc))
                raise

        with allure.step("Verify updated Last Name is persisted"):
            try:
                actual = pim_page.get_last_name_value()
                assert actual == new_last_name, (
                    f"Expected Last Name '{new_last_name}' but got '{actual}'"
                )
                result("passed",
                       f"Last Name should be '{new_last_name}'",
                       f"Last Name is '{actual}'")
            except AssertionError as exc:
                result("failed",
                       f"Last Name should be '{new_last_name}'",
                       str(exc))
                raise

    # ── TC-EDIT-003: Validation — Empty First Name ────────────────────────────

    @allure.story("Edit Employee Validation")
    @allure.title("TC-EDIT-003: Edit with empty first name — Required validation shown")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.ui
    def test_edit_employee_empty_first_name_validation(self, page):
        """
        Verify that clearing the First Name field and saving shows
        a 'Required' validation error and does NOT save the record.

        Test Data: No Excel data needed.
        """
        cloud_env = read_cloud_env()

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM Employee List"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            try:
                pim_page.verify_employee_in_list()
                result("passed", "Employee List should have at least one row",
                       f"{pim_page.get_employee_row_count()} row(s) visible")
            except Exception as exc:
                result("failed", "Employee List should have at least one row", str(exc))
                raise

        with allure.step("Click Edit on the first employee"):
            pim_page.click_edit_first_result()

        with allure.step("Clear the First Name field"):
            try:
                pim_page.update_first_name("")
                result("passed", "First Name field should be clearable", "First Name cleared")
            except Exception as exc:
                result("failed", "First Name field should be clearable", str(exc))
                raise

        with allure.step("Attempt to save with empty First Name"):
            pim_page.save_personal_details()

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify 'Required' validation error is displayed (web-first assertion)"):
            try:
                pim_page.verify_required_field_error()
                result("passed",
                       "'Required' error should appear for empty First Name",
                       "'Required' validation error is visible")
            except Exception as exc:
                result("failed",
                       "'Required' error should appear for empty First Name",
                       str(exc))
                raise

    # ── TC-EDIT-004: Navigate to Edit Page ────────────────────────────────────

    @allure.story("Edit Employee Navigation")
    @allure.title("TC-EDIT-004: Navigate to edit page — Personal Details URL confirmed")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.ui
    def test_edit_navigates_to_personal_details(self, page):
        """
        Verify that clicking the Edit button navigates to the
        Personal Details page (URL contains 'viewPersonalDetails').

        Playwright concept: wait_for_url() for navigation contract validation.
        Test Data: No Excel data needed.
        """
        cloud_env = read_cloud_env()

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM Employee List"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            try:
                pim_page.verify_employee_in_list()
                result("passed", "Employee List should have at least one row",
                       f"{pim_page.get_employee_row_count()} row(s) visible")
            except Exception as exc:
                result("failed", "Employee List should have at least one row", str(exc))
                raise

        with allure.step("Click Edit on the first employee"):
            try:
                pim_page.click_edit_first_result()
                result("passed", "Edit button clicked successfully",
                       f"Navigated to: {page.url}")
            except Exception as exc:
                result("failed", "Edit button click failed", str(exc))
                raise

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Verify URL contains 'viewPersonalDetails'"):
            try:
                assert "viewPersonalDetails" in page.url, (
                    f"Expected URL to contain 'viewPersonalDetails' but got: {page.url}"
                )
                result("passed",
                       "URL should contain 'viewPersonalDetails'",
                       f"URL is: {page.url}")
            except AssertionError as exc:
                result("failed",
                       "URL should contain 'viewPersonalDetails'",
                       str(exc))
                raise

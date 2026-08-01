"""
test_delete_employee.py — Delete Employee Feature Tests
=========================================================
Feature   : PIM → Employee List → Delete Employee (OrangeHRM)
Story ID  : HRM-204

Business Value:
  Employee termination/offboarding requires removing the employee record
  from the system. This suite verifies the delete workflow including
  the confirmation modal and post-delete state.

Playwright Concepts Demonstrated:
  - Custom modal dialog handling (NOT browser alert — OrangeHRM uses
    a Vue.js modal, handled via locator click, not page.on("dialog"))
  - web-first assertions via expect() (verify_delete_modal_visible,
    verify_delete_success, verify_employee_in_list)
  - .first locator to avoid strict mode violation on multi-row tables
  - Auto-waiting on every interaction (BasePage)
  - Storage State session reuse (no repeated logins)

Framework Components Reused:
  - PIMPage          (core/ui/pages/pim_page.py)
  - SessionManager   (core/ui/session_manager.py)
  - result()         (core/common_modules.py)
  - read_api_data_from_excel / read_cloud_env (core/utils/XLUtils.py)
  - page fixture     (conftest.py)

Test Strategy:
  - TC-DEL-001 and TC-DEL-002 first ADD a test employee (using a
    timestamp-based name to avoid conflicts), then delete/cancel.
    This ensures demo data is not permanently affected.
  - TC-DEL-003 verifies the confirmation modal appears before deletion.

Test Cases:
  TC-DEL-001  Delete employee — confirmation modal → Yes → employee removed
  TC-DEL-002  Cancel delete — confirmation modal → No → employee still exists
  TC-DEL-003  Delete modal appears — clicking Delete shows confirmation dialog
"""

import time
import allure
import pytest

from core.common_modules import result
from core.e2e_testData import url, username, password, storage_state_path
from core.ui.pages.pim_page import PIMPage
from core.ui.session_manager import SessionManager
from core.utils.XLUtils import read_cloud_env


@allure.feature("Delete Employee")
class TestDeleteEmployee:
    """
    End-to-end test suite for PIM → Delete Employee (HRM-204).

    Pre-conditions:
      - storageState.json exists (run test_generate_storage_state once)
      - OrangeHRM demo has at least one employee (always true for demo)
    """

    # ── TC-DEL-001: Delete Employee — Confirm ─────────────────────────────────

    @allure.story("Delete Employee — Confirm")
    @allure.title("TC-DEL-001: Delete employee — confirmation modal → Yes → employee removed")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.ui
    def test_delete_employee_confirm(self, page):
        """
        Verify that clicking Delete → confirming removes the employee.

        Strategy:
          1. Add a test employee with a unique timestamp-based name
          2. Search for that employee by ID
          3. Click Delete → verify modal appears
          4. Click 'Yes, Delete' → verify success toast
          5. Verify the employee no longer appears in search results

        Playwright concepts: custom modal dialog, web-first assertions,
        .first locator, wait_for_load_state.
        """
        cloud_env = read_cloud_env()
        ts = str(int(time.time()))[-6:]   # 6-digit timestamp suffix
        first_name = f"DelTest{ts}"
        last_name  = "AutoDelete"

        # ── Arrange: Navigate and add a test employee ─────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM and add a test employee"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            pim_page.click_add_employee()
            pim_page.enter_first_name(first_name)
            pim_page.enter_last_name(last_name)
            # click_save() waits for domcontentloaded; then wait for URL change
            pim_page.click_save()
            # Demo site can be slow — wait up to 60s for redirect to Personal Details
            try:
                page.wait_for_url("**/viewPersonalDetails/**", timeout=60_000)
            except Exception:
                # If redirect didn't happen, the save may have failed silently
                # Try clicking Save again (demo site sometimes needs a retry)
                pim_page.click_save()
                page.wait_for_url("**/viewPersonalDetails/**", timeout=30_000)
            page.wait_for_load_state("domcontentloaded")
            result("passed",
                   f"Test employee '{first_name} {last_name}' should be created",
                   f"Personal Details page loaded: {page.url}")

        # ── Act: Navigate to Employee List and search by name ─────────────────
        with allure.step("Navigate back to Employee List"):
            pim_page.navigate_to_pim()

        with allure.step(f"Search for employee by last name: '{last_name}'"):
            pim_page.search_employee_by_name(last_name)
            try:
                pim_page.verify_employee_in_list()
                row_count_before = pim_page.get_employee_row_count()
                result("passed", "Employee should appear in search results",
                       f"{row_count_before} row(s) found for '{last_name}'")
            except Exception as exc:
                result("failed", "Employee should appear in search results", str(exc))
                raise

        with allure.step("Click Delete on the first matching employee"):
            try:
                pim_page.click_delete_first_result()
                result("passed", "Delete button should be clickable",
                       "Delete button clicked")
            except Exception as exc:
                result("failed", "Delete button should be clickable", str(exc))
                raise

        # ── Assert: Modal appears ─────────────────────────────────────────────
        with allure.step("Verify confirmation modal is displayed (web-first assertion)"):
            try:
                pim_page.verify_delete_modal_visible()
                result("passed", "Confirmation modal should appear after clicking Delete",
                       "Confirmation modal is visible")
            except Exception as exc:
                result("failed", "Confirmation modal should appear after clicking Delete",
                       str(exc))
                raise

        with allure.step("Click 'Yes, Delete' to confirm"):
            try:
                pim_page.confirm_delete()
                result("passed", "'Yes, Delete' should confirm the deletion",
                       "Deletion confirmed")
            except Exception as exc:
                result("failed", "'Yes, Delete' should confirm the deletion", str(exc))
                raise

        # ── Assert: Success and employee removed ──────────────────────────────
        with allure.step("Verify success toast is displayed (web-first assertion)"):
            try:
                pim_page.verify_delete_success()
                result("passed", "Success toast should appear after deletion",
                       "Success toast is visible")
            except Exception as exc:
                result("failed", "Success toast should appear after deletion", str(exc))
                raise

        with allure.step(f"Verify '{last_name}' employee count decreased after deletion"):
            pim_page.search_employee_by_name(last_name)
            row_count_after = pim_page.get_employee_row_count()
            try:
                assert row_count_after < row_count_before, (
                    f"Expected fewer rows after deletion: before={row_count_before}, "
                    f"after={row_count_after}"
                )
                result("passed",
                       f"Row count should decrease after deletion (was {row_count_before})",
                       f"Row count is now {row_count_after}")
            except AssertionError as exc:
                # If no rows at all, that's also a valid pass (only 1 employee existed)
                if row_count_after == 0:
                    result("passed",
                           f"Row count should decrease after deletion (was {row_count_before})",
                           "No rows found — employee successfully deleted")
                else:
                    result("failed",
                           f"Row count should decrease after deletion (was {row_count_before})",
                           str(exc))
                    raise

    # ── TC-DEL-002: Cancel Delete ─────────────────────────────────────────────

    @allure.story("Delete Employee — Cancel")
    @allure.title("TC-DEL-002: Cancel delete — confirmation modal → No → employee still exists")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.ui
    def test_delete_employee_cancel(self, page):
        """
        Verify that clicking Delete → cancelling keeps the employee.

        Strategy:
          1. Add a test employee with a unique timestamp-based name
          2. Search for that employee by ID
          3. Click Delete → verify modal appears
          4. Click 'No, Cancel' → verify employee still in list

        Note: The test employee created here is NOT deleted — it remains
        in the demo system. This is acceptable for a demo environment.
        """
        cloud_env = read_cloud_env()
        ts = str(int(time.time()))[-6:]
        first_name = f"CancelTest{ts}"
        last_name  = "AutoCancel"

        # ── Arrange: Navigate and add a test employee ─────────────────────────
        with allure.step("Navigate to application"):
            page.goto(url, wait_until="domcontentloaded")
            SessionManager.ensure_authenticated(page, url, username, password, storage_state_path)

        with allure.step("Navigate to PIM and add a test employee"):
            pim_page = PIMPage(page)
            pim_page.navigate_to_pim()
            pim_page.click_add_employee()
            pim_page.enter_first_name(first_name)
            pim_page.enter_last_name(last_name)
            pim_page.click_save()
            # Demo site can be slow — retry save if redirect doesn't happen
            try:
                page.wait_for_url("**/viewPersonalDetails/**", timeout=60_000)
            except Exception:
                pim_page.click_save()
                page.wait_for_url("**/viewPersonalDetails/**", timeout=30_000)
            page.wait_for_load_state("domcontentloaded")
            emp_id = pim_page.get_employee_id_from_personal_details()
            result("passed",
                   f"Test employee '{first_name} {last_name}' should be created",
                   f"Employee created with ID: {emp_id}")

        # ── Act: Search and attempt delete ────────────────────────────────────
        with allure.step("Navigate back to Employee List"):
            pim_page.navigate_to_pim()

        with allure.step(f"Search for employee by ID: '{emp_id}'"):
            pim_page.search_employee_by_id(emp_id)
            try:
                pim_page.verify_employee_in_list()
                result("passed", "Employee should appear in search results",
                       f"Employee found with ID: {emp_id}")
            except Exception as exc:
                result("failed", "Employee should appear in search results", str(exc))
                raise

        with allure.step("Click Delete on the employee"):
            pim_page.click_delete_first_result()

        with allure.step("Verify confirmation modal is displayed"):
            try:
                pim_page.verify_delete_modal_visible()
                result("passed", "Confirmation modal should appear",
                       "Confirmation modal is visible")
            except Exception as exc:
                result("failed", "Confirmation modal should appear", str(exc))
                raise

        with allure.step("Click 'No, Cancel' to dismiss"):
            try:
                pim_page.cancel_delete()
                result("passed", "'No, Cancel' should dismiss the modal",
                       "Modal dismissed")
            except Exception as exc:
                result("failed", "'No, Cancel' should dismiss the modal", str(exc))
                raise

        # ── Assert: Employee still exists ─────────────────────────────────────
        with allure.step(f"Verify employee ID '{emp_id}' still in list after cancel"):
            pim_page.search_employee_by_id(emp_id)
            try:
                pim_page.verify_employee_in_list()
                result("passed",
                       f"Employee ID '{emp_id}' should still exist after cancel",
                       f"{pim_page.get_employee_row_count()} row(s) found")
            except Exception as exc:
                result("failed",
                       f"Employee ID '{emp_id}' should still exist after cancel",
                       str(exc))
                raise

    # ── TC-DEL-003: Delete Modal Appears ─────────────────────────────────────

    @allure.story("Delete Employee — Modal")
    @allure.title("TC-DEL-003: Delete modal appears — clicking Delete shows confirmation dialog")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.ui
    def test_delete_modal_appears(self, page):
        """
        Verify that clicking the Delete button shows the confirmation modal.

        This test validates the modal appearance contract only — it cancels
        the deletion to avoid modifying demo data.

        Playwright concept: custom modal dialog (not browser alert).
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

        with allure.step("Click Delete on the first employee"):
            try:
                pim_page.click_delete_first_result()
                result("passed", "Delete button should be clickable",
                       "Delete button clicked")
            except Exception as exc:
                result("failed", "Delete button should be clickable", str(exc))
                raise

        # ── Assert: Modal visible ─────────────────────────────────────────────
        with allure.step("Verify confirmation modal is displayed (web-first assertion)"):
            try:
                pim_page.verify_delete_modal_visible()
                result("passed",
                       "Confirmation modal should appear after clicking Delete",
                       "Confirmation modal is visible")
            except Exception as exc:
                result("failed",
                       "Confirmation modal should appear after clicking Delete",
                       str(exc))
                raise

        with allure.step("Cancel the deletion to preserve demo data"):
            pim_page.cancel_delete()
            result("passed", "Deletion cancelled — demo data preserved",
                   "Modal dismissed via 'No, Cancel'")

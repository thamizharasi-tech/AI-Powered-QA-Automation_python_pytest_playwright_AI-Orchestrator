"""
Automation Agent
================
Generates production-ready Pytest + Playwright test scripts that fully
integrate with the existing QA automation framework.

Reuses: POM classes, conftest page fixture, XLUtils, result(), Allure decorators.
"""


class AutomationAgent:
    """Generate production-ready Pytest + Playwright automation scripts."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def generate_script(self, test_cases: str) -> str:
        prompt = f"""
You are a Senior Test Automation Architect specializing in Python, Pytest,
Playwright, and Data-Driven Testing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FRAMEWORK ARCHITECTURE — YOU MUST REUSE THESE COMPONENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PAGE OBJECT MODEL (POM)
   BasePage (core/ui/pages/base_page.py): click, fill, get_text, is_visible
   LoginPage (core/ui/pages/login_page.py): enter_username, enter_password, click_login, login, verify_dashboard
   DashboardPage (core/ui/pages/dashboard_page.py): verify_dashboard, navigate_to_admin, navigate_to_pim
   LeftMenu (core/ui/components/left_menu.py): click_admin, click_pim, click_leave, etc.

2. LOCATORS
   LoginLocator: USERNAME, PASSWORD, LOGIN_BUTTON, DASHBOARD_TITLE
   DashboardLocator, PimLocator (see core/ui/locators/)

3. FIXTURES (conftest.py)
   `page` fixture — inject as test parameter, DO NOT create your own browser

4. EXCEL TEST DATA (core/utils/XLUtils.py)
   read_api_data_from_excel(sheet_name, testcase_name) -> dict
   read_cloud_env() -> str

5. CONFIGURATION (core/e2e_testData.py)
   from core.e2e_testData import url, username, password, storage_state_path

6. RESULT LOGGING (core/common_modules.py)
   result(status, expected_behaviour, actual_behaviour)
   status: "passed" | "failed" | "verificationPassed" | "verificationFailed"

7. SESSION MANAGEMENT (core/ui/session_manager.py)
   SessionManager.save_storage_state(page, storage_state_path)
   SessionManager.storage_state_exists(storage_state_path) -> bool

8. ALLURE REPORTING
   @allure.feature("Feature Name")  ← on class
   @allure.story("Story Name")      ← on method
   @allure.title("TC-XXX: Desc")   ← on method
   @allure.severity(allure.severity_level.CRITICAL)
   with allure.step("Step description"):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CODING STANDARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Use the `page` fixture from conftest.py — never create your own browser
  - Read ALL test data from Excel using read_api_data_from_excel()
  - Wrap every logical step in `with allure.step("...")`
  - Use result() from common_modules for all pass/fail logging
  - Use try/except around assertions and call result("failed",...) before raise
  - Follow PEP8: 4-space indent, snake_case methods, PascalCase classes
  - Group tests in a class named Test<Feature>
  - Use @allure.feature on the class and @allure.story/@allure.title on each method
  - Add Arrange / Act / Assert comments in each test

❌ DO NOT:
  - Import sync_playwright or create browsers manually
  - Hardcode URLs, usernames, passwords, or file paths
  - Duplicate methods that already exist in BasePage, LoginPage, or DashboardPage
  - Use time.sleep() — use Playwright's built-in waits

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST CASES TO AUTOMATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{test_cases}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY a complete, runnable Python file with:
  1. Module-level docstring listing all framework components reused
  2. All required imports
  3. A single test class with @allure.feature decorator
  4. One test method per test case with all required decorators
  5. PEP8 compliant code

CRITICAL NAMING RULES:
  - @allure.feature("...") MUST reflect the ACTUAL feature being tested
  - Class name MUST be Test<FeatureName> matching the feature
  - The LOGIN examples above are ONLY structural templates — replace with actual feature

Do NOT include any explanation, markdown fences, or text outside the Python file.
"""
        return self.llm.generate(prompt)

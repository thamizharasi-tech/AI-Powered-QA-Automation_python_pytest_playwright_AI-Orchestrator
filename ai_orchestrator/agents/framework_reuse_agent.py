"""
Framework Reuse Agent
=====================
Senior SDET agent that analyzes the existing automation framework BEFORE
code generation to identify reusable components, prevent duplication,
and guide the AutomationAgent to extend rather than recreate.

Responsibilities:
  - Scan existing page objects, API clients, fixtures, utilities
  - Identify which existing components can be reused for the new requirement
  - Detect potential duplicate test files or test methods
  - Recommend the exact import paths and method signatures to reuse
  - Flag components that need extension vs. creation from scratch
  - Produce a reuse report consumed by AutomationAgent

Pipeline Position:
  Runs AFTER AutomationRecommendationAgent, BEFORE AutomationAgent.
  Output is injected into AutomationAgent's context to guide code generation.

Architectural Principle:
  REUSE > EXTEND > CREATE NEW
  The LLM must never generate code that duplicates existing framework components.
"""

from pathlib import Path


# Complete framework component inventory with method signatures
_COMPONENT_INVENTORY = {
    "page_objects": {
        "LoginPage": {
            "file": "core/ui/pages/login_page.py",
            "import": "from core.ui.pages.login_page import LoginPage",
            "methods": [
                "login_page.enter_username(username: str)",
                "login_page.enter_password(password: str)",
                "login_page.click_login()",
                "login_page.login(username, password)  # combined helper",
                "login_page.verify_dashboard()  # asserts dashboard title visible",
            ],
        },
        "DashboardPage": {
            "file": "core/ui/pages/dashboard_page.py",
            "import": "from core.ui.pages.dashboard_page import DashboardPage",
            "methods": [
                "dashboard.verify_dashboard() -> bool",
                "dashboard.navigate_to_admin()",
                "dashboard.navigate_to_pim()",
                "dashboard.navigate_to_leave()",
            ],
        },
        "BasePage": {
            "file": "core/ui/pages/base_page.py",
            "import": "from core.ui.pages.base_page import BasePage",
            "methods": [
                "self.click(locator)",
                "self.fill(locator, value)",
                "self.get_text(locator) -> str",
                "self.is_visible(locator, timeout=5000) -> bool",
            ],
        },
        "PimPage": {
            "file": "core/ui/pages/pim_page.py",
            "import": "from core.ui.pages.pim_page import PimPage",
            "methods": ["(see pim_page.py for available methods)"],
        },
    },
    "components": {
        "LeftMenu": {
            "file": "core/ui/components/left_menu.py",
            "import": "from core.ui.components.left_menu import LeftMenu",
            "methods": [
                "left_menu.click_admin()",
                "left_menu.click_pim()",
                "left_menu.click_leave()",
                "left_menu.click_time()",
                "left_menu.click_recruitment()",
                "left_menu.click_dashboard()",
                "left_menu.click_directory()",
                "left_menu.click_claim()",
                "left_menu.click_buzz()",
            ],
        },
    },
    "locators": {
        "LoginLocator": {
            "file": "core/ui/locators/login_locator.py",
            "import": "from core.ui.locators.login_locator import LoginLocator",
            "constants": [
                "LoginLocator.USERNAME = \"input[name='username']\"",
                "LoginLocator.PASSWORD = \"input[name='password']\"",
                "LoginLocator.LOGIN_BUTTON = \"button[type='submit']\"",
                "LoginLocator.DASHBOARD_TITLE = \"//h6[text()='Dashboard']\"",
            ],
        },
        "DashboardLocator": {
            "file": "core/ui/locators/dashboard_locator.py",
            "import": "from core.ui.locators.dashboard_locator import DashboardLocator",
        },
        "PimLocator": {
            "file": "core/ui/locators/pim_locator.py",
            "import": "from core.ui.locators.pim_locator import PimLocator",
        },
    },
    "utilities": {
        "XLUtils": {
            "file": "core/utils/XLUtils.py",
            "import": "from core.utils.XLUtils import read_api_data_from_excel, read_cloud_env",
            "methods": [
                "read_api_data_from_excel(sheet_name, testcase_name) -> dict",
                "read_cloud_env() -> str",
                "get_excel_rows(sheet_name, row_names) -> list",
            ],
        },
        "common_modules": {
            "file": "core/common_modules.py",
            "import": "from core.common_modules import result",
            "methods": [
                "result(status, expected, actual)  # status: passed|failed|verificationPassed|verificationFailed",
            ],
        },
        "SessionManager": {
            "file": "core/ui/session_manager.py",
            "import": "from core.ui.session_manager import SessionManager",
            "methods": [
                "SessionManager.save_storage_state(page, storage_state_path)",
                "SessionManager.storage_state_exists(storage_state_path) -> bool",
            ],
        },
        "e2e_testData": {
            "file": "core/e2e_testData.py",
            "import": "from core.e2e_testData import url, username, password, storage_state_path",
            "exports": ["url", "username", "password", "storage_state_path", "browser_name"],
        },
    },
    "api_clients": {
        "api_client": {
            "file": "core/api/api_client.py",
            "import": "from core.api.api_client import create_user, update_user, get_user, delete_user",
            "methods": [
                "create_user(cloud_env, id, username, firstname, lastname, email, password, phone, userstatus, tc)",
                "update_user(cloud_env, id, username, firstname, lastname, email, password, phone, userstatus, tc)",
                "get_user(cloud_env, username, tc)",
                "delete_user(cloud_env, username, tc)",
            ],
        },
    },
    "fixtures": {
        "page": {
            "file": "conftest.py",
            "usage": "def test_example(self, page):  # inject as test parameter",
            "notes": "DO NOT create your own browser. Use this fixture only.",
        },
    },
    "existing_tests": [
        "tests/ui/test_feature_login.py",
        "tests/ui/test_login.py",
        "tests/ui/test_add_employee.py",
        "tests/ui/test_employee_search.py",
        "tests/ui/test_user_management.py",
        "tests/api/test_positive_user_creation.py",
    ],
}


class FrameworkReuseAgent:
    """
    Analyze the existing framework and produce a reuse report to guide
    the AutomationAgent in generating non-duplicate, framework-integrated code.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def analyze(self, requirement: str, key_scenarios: str, recommendation: str) -> str:
        """
        Identify reusable framework components for the given scenarios.

        Parameters
        ----------
        requirement : str
            Original raw requirement text.
        key_scenarios : str
            KeyScenarioAgent output (KS-XXX with automation type).
        recommendation : str
            AutomationRecommendationAgent output (AUTOMATE decisions).

        Returns
        -------
        str
            Framework reuse report with specific import paths, method
            signatures, and duplication warnings for AutomationAgent.
        """
        inventory_text = self._format_inventory()

        prompt = f"""
You are a Senior SDET and Framework Architect with 15+ years of experience
building and maintaining enterprise automation frameworks. You are the
guardian of code quality and framework consistency.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before any automation code is generated, analyze the existing framework
and identify EXACTLY which components can be reused. Produce a precise
reuse report that the AutomationAgent will use to avoid duplication.

Principle: REUSE > EXTEND > CREATE NEW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY SCENARIOS TO AUTOMATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{key_scenarios}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOMATION RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXISTING FRAMEWORK INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{inventory_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. REUSE SUMMARY

  Components to Reuse  : [N]
  Components to Extend : [N]
  Components to Create : [N]
  Duplicate Risk       : [HIGH | MEDIUM | LOW | NONE]

## 2. REUSABLE COMPONENTS (use these directly — DO NOT recreate)

For each reusable component:

─────────────────────────────────────────────────────────────────────────────
Component     : [Class/Function name]
File          : [Exact file path]
Import        : [Exact import statement]
Methods/Usage : [Exact method calls to use]
Scenario      : [KS-XXX that uses this component]
─────────────────────────────────────────────────────────────────────────────

## 3. COMPONENTS TO EXTEND (extend existing, do not replace)

For each component that needs extension:

─────────────────────────────────────────────────────────────────────────────
Component     : [Class name]
File          : [Exact file path]
Extension     : [What new method/property to add]
Reason        : [Why extension is needed instead of reuse]
─────────────────────────────────────────────────────────────────────────────

## 4. NEW COMPONENTS REQUIRED (create only if no reusable alternative exists)

For each new component:

─────────────────────────────────────────────────────────────────────────────
Component     : [Proposed class/function name]
File          : [Proposed file path]
Reason        : [Why no existing component can be reused or extended]
Pattern       : [Follow existing pattern from: file_path]
─────────────────────────────────────────────────────────────────────────────

## 5. DUPLICATION WARNINGS

List any existing test files that cover similar scenarios:
  ⚠️ [Existing file] covers [scenario] — ensure new test does not duplicate

## 6. AUTOMATION AGENT INSTRUCTIONS

Provide specific instructions for the AutomationAgent:
  - MUST USE: [list of exact imports and method calls]
  - MUST NOT CREATE: [list of things that already exist]
  - MUST EXTEND: [list of files to add methods to]
  - TARGET FILE: [tests/ui/test_<feature>.py or tests/api/test_<feature>.py]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Provide exact import statements (copy-paste ready)
  - Reference specific method signatures from the inventory
  - Flag any scenario where a duplicate test file might be created
  - Be specific about what to reuse vs. what to create

❌ DO NOT:
  - Recommend creating a new LoginPage if LoginPage already exists
  - Recommend creating a new `page` fixture — it's in conftest.py
  - Recommend hardcoding URLs or credentials
  - Skip the Automation Agent Instructions section
"""
        return self.llm.generate(prompt)

    def _format_inventory(self) -> str:
        """Format the component inventory for the prompt."""
        import json
        return json.dumps(_COMPONENT_INVENTORY, indent=2)

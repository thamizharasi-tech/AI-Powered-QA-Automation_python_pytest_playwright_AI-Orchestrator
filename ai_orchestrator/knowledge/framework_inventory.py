"""
Framework Inventory
===================
Static knowledge base of the existing QA automation framework.

This module provides a single source of truth about what exists in the
framework so that:
  1. ImpactAnalyzer can identify which components are affected by a change
  2. FrameworkReuseAgent can identify what to reuse before code generation
  3. AutomationAgent gets accurate component information in its prompt
  4. The pipeline never generates duplicate components

This inventory is maintained manually and updated when new components
are added to the framework. It does NOT call the LLM.

Architectural Principle:
  CODE VALIDATES — deterministic inventory prevents LLM from inventing
  components that don't exist or missing components that do.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FrameworkComponent:
    """Represents a single reusable framework component."""
    name: str
    file_path: str
    import_statement: str
    component_type: str          # page_object | component | locator | utility | api_client | fixture
    description: str
    methods: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)  # e.g. ["login", "auth", "ui"]

    def exists(self) -> bool:
        """Return True if the component file exists on disk."""
        return Path(self.file_path).exists()

    def to_prompt_text(self) -> str:
        """Format component info for inclusion in an LLM prompt."""
        lines = [
            f"Component : {self.name}",
            f"File      : {self.file_path}",
            f"Import    : {self.import_statement}",
        ]
        if self.methods:
            lines.append("Methods   :")
            for m in self.methods:
                lines.append(f"  - {m}")
        if self.constants:
            lines.append("Constants :")
            for c in self.constants:
                lines.append(f"  - {c}")
        return "\n".join(lines)


@dataclass
class TestFile:
    """Represents an existing test file."""
    file_path: str
    test_class: str
    feature: str
    test_methods: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def exists(self) -> bool:
        return Path(self.file_path).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Framework Inventory — single source of truth
# ─────────────────────────────────────────────────────────────────────────────

FRAMEWORK_COMPONENTS: Dict[str, FrameworkComponent] = {

    # ── Page Objects ──────────────────────────────────────────────────────────

    "LoginPage": FrameworkComponent(
        name="LoginPage",
        file_path="core/ui/pages/login_page.py",
        import_statement="from core.ui.pages.login_page import LoginPage",
        component_type="page_object",
        description="Login page POM — handles authentication flows",
        methods=[
            "login_page.enter_username(username: str)",
            "login_page.enter_password(password: str)",
            "login_page.click_login()",
            "login_page.login(username, password)  # combined helper",
            "login_page.verify_dashboard()  # asserts dashboard title visible",
        ],
        tags=["login", "auth", "ui"],
    ),

    "DashboardPage": FrameworkComponent(
        name="DashboardPage",
        file_path="core/ui/pages/dashboard_page.py",
        import_statement="from core.ui.pages.dashboard_page import DashboardPage",
        component_type="page_object",
        description="Dashboard page POM — post-login navigation",
        methods=[
            "dashboard.verify_dashboard() -> bool",
            "dashboard.navigate_to_admin()",
            "dashboard.navigate_to_pim()",
            "dashboard.navigate_to_leave()",
        ],
        tags=["dashboard", "navigation", "ui"],
    ),

    "BasePage": FrameworkComponent(
        name="BasePage",
        file_path="core/ui/pages/base_page.py",
        import_statement="from core.ui.pages.base_page import BasePage",
        component_type="page_object",
        description="Base page class — generic UI interactions",
        methods=[
            "self.click(locator)",
            "self.fill(locator, value)",
            "self.get_text(locator) -> str",
            "self.is_visible(locator, timeout=5000) -> bool",
        ],
        tags=["base", "ui", "generic"],
    ),

    "PimPage": FrameworkComponent(
        name="PimPage",
        file_path="core/ui/pages/pim_page.py",
        import_statement="from core.ui.pages.pim_page import PimPage",
        component_type="page_object",
        description="PIM (Personnel Information Management) page POM",
        methods=["(see pim_page.py for available methods)"],
        tags=["pim", "employee", "ui"],
    ),

    "LeaveApplyPage": FrameworkComponent(
        name="LeaveApplyPage",
        file_path="core/ui/pages/leave_page.py",
        import_statement="from core.ui.pages.leave_page import LeaveApplyPage",
        component_type="page_object",
        description="Leave Apply page POM — apply for leave form",
        methods=[
            "leave_page.navigate_to_apply_leave()",
            "leave_page.select_leave_type(leave_type: str)",
            "leave_page.enter_from_date(date_value: str)",
            "leave_page.enter_to_date(date_value: str)",
            "leave_page.enter_comments(comments: str)",
            "leave_page.click_apply()",
            "leave_page.apply_leave(leave_type, from_date, to_date, comments='')  # combined helper",
            "leave_page.is_success_shown() -> bool",
            "leave_page.is_error_shown() -> bool",
            "leave_page.is_validation_error_shown() -> bool",
            "leave_page.get_error_text() -> str",
            "leave_page.get_balance_text() -> str",
        ],
        tags=["leave", "ui"],
    ),

    "MyLeavePage": FrameworkComponent(
        name="MyLeavePage",
        file_path="core/ui/pages/leave_page.py",
        import_statement="from core.ui.pages.leave_page import MyLeavePage",
        component_type="page_object",
        description="My Leave list page POM — view submitted leave requests",
        methods=[
            "my_leave.navigate_to_my_leave()",
            "my_leave.find_leave_request(leave_type, from_date, to_date) -> bool",
            "my_leave.get_leave_status(leave_type, from_date) -> str",
        ],
        tags=["leave", "ui"],
    ),

    # ── Components ────────────────────────────────────────────────────────────

    "LeftMenu": FrameworkComponent(
        name="LeftMenu",
        file_path="core/ui/components/left_menu.py",
        import_statement="from core.ui.components.left_menu import LeftMenu",
        component_type="component",
        description="Left navigation menu component",
        methods=[
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
        tags=["navigation", "menu", "ui"],
    ),

    # ── Locators ──────────────────────────────────────────────────────────────

    "LoginLocator": FrameworkComponent(
        name="LoginLocator",
        file_path="core/ui/locators/login_locator.py",
        import_statement="from core.ui.locators.login_locator import LoginLocator",
        component_type="locator",
        description="Login page element selectors",
        constants=[
            "LoginLocator.USERNAME = \"input[name='username']\"",
            "LoginLocator.PASSWORD = \"input[name='password']\"",
            "LoginLocator.LOGIN_BUTTON = \"button[type='submit']\"",
            "LoginLocator.DASHBOARD_TITLE = \"//h6[text()='Dashboard']\"",
        ],
        tags=["login", "locator", "ui"],
    ),

    "DashboardLocator": FrameworkComponent(
        name="DashboardLocator",
        file_path="core/ui/locators/dashboard_locator.py",
        import_statement="from core.ui.locators.dashboard_locator import DashboardLocator",
        component_type="locator",
        description="Dashboard page element selectors",
        tags=["dashboard", "locator", "ui"],
    ),

    "PimLocator": FrameworkComponent(
        name="PimLocator",
        file_path="core/ui/locators/pim_locator.py",
        import_statement="from core.ui.locators.pim_locator import PimLocator",
        component_type="locator",
        description="PIM page element selectors",
        tags=["pim", "locator", "ui"],
    ),

    # ── Utilities ─────────────────────────────────────────────────────────────

    "XLUtils": FrameworkComponent(
        name="XLUtils",
        file_path="core/utils/XLUtils.py",
        import_statement="from core.utils.XLUtils import read_api_data_from_excel, read_cloud_env",
        component_type="utility",
        description="Excel test data reader — reads rows from API_testData.xlsx",
        methods=[
            "read_api_data_from_excel(sheet_name, testcase_name) -> dict",
            "read_cloud_env() -> str",
            "get_excel_rows(sheet_name, row_names) -> list",
            "save_api_resp_in_excel(sheet_name, testcase_name, data)",
        ],
        tags=["excel", "test-data", "utility"],
    ),

    "common_modules": FrameworkComponent(
        name="common_modules",
        file_path="core/common_modules.py",
        import_statement="from core.common_modules import result",
        component_type="utility",
        description="Shared utilities — result() for pass/fail logging",
        methods=[
            "result(status, expected, actual)  # status: passed|failed|verificationPassed|verificationFailed",
            "log_backup(file, cloud_env)",
        ],
        tags=["logging", "assertion", "utility"],
    ),

    "SessionManager": FrameworkComponent(
        name="SessionManager",
        file_path="core/ui/session_manager.py",
        import_statement="from core.ui.session_manager import SessionManager",
        component_type="utility",
        description="Browser session state management",
        methods=[
            "SessionManager.save_storage_state(page, storage_state_path)",
            "SessionManager.storage_state_exists(storage_state_path) -> bool",
        ],
        tags=["session", "auth", "browser", "utility"],
    ),

    "e2e_testData": FrameworkComponent(
        name="e2e_testData",
        file_path="core/e2e_testData.py",
        import_statement="from core.e2e_testData import url, username, password, storage_state_path",
        component_type="utility",
        description="Central path registry and test configuration",
        constants=[
            "url — application base URL",
            "username — default login username",
            "password — default login password",
            "storage_state_path — path to storageState.json",
            "browser_name — configured browser (chromium/firefox/edge)",
        ],
        tags=["config", "paths", "utility"],
    ),

    # ── API Clients ───────────────────────────────────────────────────────────

    "api_client": FrameworkComponent(
        name="api_client",
        file_path="core/api/api_client.py",
        import_statement="from core.api.api_client import create_user, update_user, get_user, delete_user",
        component_type="api_client",
        description="REST API client — Petstore API operations",
        methods=[
            "create_user(cloud_env, id, username, firstname, lastname, email, password, phone, userstatus, tc)",
            "update_user(cloud_env, id, username, firstname, lastname, email, password, phone, userstatus, tc)",
            "get_user(cloud_env, username, tc)",
            "delete_user(cloud_env, username, tc)",
        ],
        tags=["api", "rest", "user"],
    ),

    # ── Fixtures ──────────────────────────────────────────────────────────────

    "page_fixture": FrameworkComponent(
        name="page (fixture)",
        file_path="conftest.py",
        import_statement="# Injected automatically by pytest — no import needed",
        component_type="fixture",
        description=(
            "Playwright page fixture — provides a fully configured browser page. "
            "DO NOT create your own browser. Use this fixture only."
        ),
        methods=[
            "def test_example(self, page):  # inject as test parameter",
            "page.goto(url)",
        ],
        tags=["playwright", "browser", "fixture"],
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Existing test files inventory
# ─────────────────────────────────────────────────────────────────────────────

EXISTING_TEST_FILES: List[TestFile] = [
    TestFile(
        file_path="tests/ui/test_feature_login.py",
        test_class="TestFeatureLogin",
        feature="Login",
        tags=["login", "auth", "ui"],
    ),
    TestFile(
        file_path="tests/ui/test_login.py",
        test_class="TestLogin",
        feature="Login",
        tags=["login", "auth", "ui"],
    ),
    TestFile(
        file_path="tests/ui/test_add_employee.py",
        test_class="TestAddEmployee",
        feature="Add Employee",
        tags=["employee", "pim", "ui"],
    ),
    TestFile(
        file_path="tests/ui/test_employee_search.py",
        test_class="TestEmployeeSearch",
        feature="Employee Search",
        tags=["employee", "search", "pim", "ui"],
    ),
    TestFile(
        file_path="tests/ui/test_user_management.py",
        test_class="TestUserManagement",
        feature="User Management",
        tags=["user", "admin", "ui"],
    ),
    TestFile(
        file_path="tests/api/test_positive_user_creation.py",
        test_class="TestPositiveUserCreation",
        feature="User Creation API",
        tags=["user", "api", "positive"],
    ),
    TestFile(
        file_path="tests/test_ci_smoke.py",
        test_class="(module-level functions)",
        feature="CI Smoke",
        tags=["smoke", "ci", "imports"],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_components_by_tag(tag: str) -> List[FrameworkComponent]:
    """Return all components tagged with the given tag."""
    return [c for c in FRAMEWORK_COMPONENTS.values() if tag in c.tags]


def get_components_by_type(component_type: str) -> List[FrameworkComponent]:
    """Return all components of the given type."""
    return [c for c in FRAMEWORK_COMPONENTS.values() if c.component_type == component_type]


def get_test_files_by_tag(tag: str) -> List[TestFile]:
    """Return all test files tagged with the given tag."""
    return [t for t in EXISTING_TEST_FILES if tag in t.tags]


def find_similar_test_files(feature_keywords: List[str]) -> List[TestFile]:
    """
    Find existing test files that might cover similar features.
    Used by FrameworkReuseAgent to detect potential duplicates.
    """
    results = []
    for test_file in EXISTING_TEST_FILES:
        for keyword in feature_keywords:
            if (keyword.lower() in test_file.feature.lower() or
                    any(keyword.lower() in tag for tag in test_file.tags)):
                if test_file not in results:
                    results.append(test_file)
    return results


def format_inventory_for_prompt() -> str:
    """
    Format the complete framework inventory as text for LLM prompts.
    Used by ImpactAnalyzer and FrameworkReuseAgent.
    """
    lines = ["=== EXISTING FRAMEWORK COMPONENTS ===\n"]

    by_type: Dict[str, List[FrameworkComponent]] = {}
    for comp in FRAMEWORK_COMPONENTS.values():
        by_type.setdefault(comp.component_type, []).append(comp)

    for comp_type, components in sorted(by_type.items()):
        lines.append(f"\n{comp_type.upper().replace('_', ' ')}S:")
        for comp in components:
            lines.append(f"\n  {comp.name}")
            lines.append(f"    File   : {comp.file_path}")
            lines.append(f"    Import : {comp.import_statement}")
            if comp.methods:
                lines.append("    Methods:")
                for m in comp.methods[:3]:  # Show first 3 methods
                    lines.append(f"      - {m}")
            if comp.constants:
                lines.append("    Constants:")
                for c in comp.constants[:3]:
                    lines.append(f"      - {c}")

    lines.append("\n\n=== EXISTING TEST FILES ===\n")
    for test_file in EXISTING_TEST_FILES:
        lines.append(f"  {test_file.file_path}")
        lines.append(f"    Class   : {test_file.test_class}")
        lines.append(f"    Feature : {test_file.feature}")
        lines.append(f"    Tags    : {', '.join(test_file.tags)}")

    return "\n".join(lines)

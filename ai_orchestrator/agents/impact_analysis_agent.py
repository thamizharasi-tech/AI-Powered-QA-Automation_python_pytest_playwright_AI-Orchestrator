"""
Impact Analyzer Agent
=====================
Senior SDET / Test Architect agent that performs impact analysis to identify
which existing modules, tests, APIs, and components are affected by a new
requirement or change.

Responsibilities:
  - Identify all system areas impacted by the requirement
  - Map impact to existing test files in the framework
  - Identify regression risk areas
  - Recommend which existing tests must be re-run
  - Flag integration points that need additional testing
  - Classify impact by layer (UI / API / Database / Auth / Integration)

Pipeline Position:
  Runs AFTER AmbiguityAnalyzer (status=CLEAR), BEFORE KeyScenarioAgent.
  Output feeds into: TestStrategy, AutomationRecommendationAgent, RTMAgent.

Architectural Principle:
  AI DECIDES which areas are impacted based on requirement analysis.
  CODE VALIDATES by cross-referencing the framework inventory.
  The framework continues to work if this agent is unavailable.
"""

from pathlib import Path


# Static inventory of the existing framework — updated by FrameworkReuseAgent
_FRAMEWORK_INVENTORY = {
    "ui_pages": [
        "core/ui/pages/login_page.py",
        "core/ui/pages/dashboard_page.py",
        "core/ui/pages/base_page.py",
        "core/ui/pages/pim_page.py",
    ],
    "ui_components": [
        "core/ui/components/left_menu.py",
    ],
    "locators": [
        "core/ui/locators/login_locator.py",
        "core/ui/locators/dashboard_locator.py",
        "core/ui/locators/pim_locator.py",
    ],
    "api_clients": [
        "core/api/api_client.py",
    ],
    "utilities": [
        "core/utils/XLUtils.py",
        "core/common_modules.py",
        "core/e2e_testData.py",
        "core/ui/session_manager.py",
    ],
    "existing_tests": [
        "tests/ui/test_feature_login.py",
        "tests/ui/test_login.py",
        "tests/ui/test_add_employee.py",
        "tests/ui/test_employee_search.py",
        "tests/ui/test_user_management.py",
        "tests/api/test_positive_user_creation.py",
        "tests/test_ci_smoke.py",
    ],
}


class ImpactAnalyzer:
    """
    Identify all system areas impacted by a requirement and map to existing
    framework components and test files.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def analyze(self, requirement: str, analysis: str) -> str:
        """
        Perform impact analysis for the given requirement.

        Parameters
        ----------
        requirement : str
            Original raw requirement text.
        analysis : str
            Structured analysis from StoryAnalyzer (REQ-XXX anchors).

        Returns
        -------
        str
            Structured impact analysis report with affected areas,
            regression risks, and existing test mapping.
        """
        # Build a formatted inventory string for the prompt
        inventory_text = self._format_inventory()

        prompt = f"""
You are a Senior SDET and Test Architect with 15+ years of experience in
impact analysis, regression strategy, and test coverage planning for
enterprise applications. You understand system architecture, integration
points, and how changes ripple through a codebase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Perform a comprehensive impact analysis for the requirement below.
Identify ALL system areas, components, and existing tests that are affected.
This analysis drives regression test selection and integration test scope.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURED ANALYSIS (REQ-XXX anchors)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXISTING FRAMEWORK INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{inventory_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPACT LAYERS TO ANALYZE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyze impact across ALL applicable layers:
  UI           — Browser-based user interface changes
  API          — REST API endpoints affected
  DATABASE     — Data model, schema, or query changes
  AUTH         — Authentication or authorization changes
  INTEGRATION  — Cross-service or cross-module interactions
  MESSAGING    — Kafka, MQTT, or event-driven components
  MOBILE       — Mobile app impact (if applicable)
  PERFORMANCE  — Load, throughput, or response time impact
  SECURITY     — Security posture changes
  REGRESSION   — Existing functionality at risk of breaking

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. IMPACT SUMMARY

  Total Impact Areas   : [N]
  High Impact Areas    : [N]
  Medium Impact Areas  : [N]
  Low Impact Areas     : [N]
  Regression Risk      : [HIGH | MEDIUM | LOW]
  Existing Tests Affected: [N]

## 2. IMPACTED AREAS (by layer)

For each impacted area:

─────────────────────────────────────────────────────────────────────────────
IMPACT-[NNN]
  Layer         : [UI | API | DATABASE | AUTH | INTEGRATION | MESSAGING | PERFORMANCE | SECURITY | REGRESSION]
  Component     : [Specific component, module, or service name]
  Requirement   : [REQ-XXX]
  Impact Level  : [HIGH | MEDIUM | LOW]
  Description   : [What specifically is impacted and how]
  Test Coverage : [EXISTING_TEST_COVERS | NEW_TEST_NEEDED | MANUAL_ONLY]
  Existing Test : [Path to existing test file if applicable, or "None"]
─────────────────────────────────────────────────────────────────────────────

## 3. REGRESSION RISK ASSESSMENT

List all existing tests that MUST be re-run due to this change:

  | Test File | Test Type | Regression Risk | Reason |
  |-----------|-----------|-----------------|--------|
  | tests/ui/test_login.py | UI E2E | HIGH | Login flow may be affected |

## 4. INTEGRATION POINTS

List all integration points that need additional testing:
  - [Service/Component A] ↔ [Service/Component B]: [Why this integration is at risk]

## 5. NEW TEST COVERAGE REQUIRED

List areas that need NEW test cases (not covered by existing tests):
  - [Area]: [What needs to be tested] — Suggested test type: [UI_E2E | API | INTEGRATION]

## 6. IMPACT MATRIX

| REQ-ID  | UI | API | DB | Auth | Integration | Regression Risk |
|---------|----|----|-----|------|-------------|-----------------|
| REQ-001 | ✅ | ✅ | ❌  | ✅   | ✅          | HIGH            |

## 7. RECOMMENDED TEST EXECUTION ORDER

Based on impact analysis, recommend the order to run tests:
  1. [Test type/area] — Reason: [Why this should run first]
  2. [Test type/area] — Reason: [Why this should run second]
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Reference specific files from the framework inventory where applicable
  - Be specific about WHY each area is impacted
  - Distinguish between direct impact and indirect/regression impact
  - Link every impact to a REQ-XXX from the analysis

❌ DO NOT:
  - List areas that are clearly NOT impacted by this requirement
  - Use vague impact descriptions like "may be affected"
  - Skip the regression risk assessment
  - Omit the impact matrix
"""
        return self.llm.generate(prompt)

    def _format_inventory(self) -> str:
        """Format the framework inventory for inclusion in the prompt."""
        lines = []
        for category, items in _FRAMEWORK_INVENTORY.items():
            lines.append(f"\n{category.upper().replace('_', ' ')}:")
            for item in items:
                lines.append(f"  - {item}")
        return "\n".join(lines)

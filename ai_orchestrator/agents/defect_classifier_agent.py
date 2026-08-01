"""
Defect Classifier Agent
=======================
Senior QA Engineer / Failure Intelligence agent that analyzes test execution
results AFTER pytest runs and classifies failures by root cause, defect type,
component, and severity.

This is distinct from DefectPredictionAgent (which predicts BEFORE execution).
This agent analyzes ACTUAL failures AFTER execution.

Responsibilities:
  - Parse test execution results (from TestReportAnalyzerAgent)
  - Classify each failure by root cause category
  - Identify patterns across multiple failures (same component, same type)
  - Distinguish between test defects (bad test) and product defects (bad code)
  - Generate defect reports with reproduction steps
  - Recommend defect priority and assignment
  - Update RTM with actual execution status

Pipeline Position:
  Runs AFTER pytest execution and TestReportAnalyzerAgent.
  Output feeds into: RTM update, SprintSummaryAgent, AI Dashboard.

Architectural Principle:
  AI DECIDES root cause classification using LLM reasoning.
  CODE VALIDATES by cross-referencing with deterministic pattern matching.
  The framework works without this agent (execution results are still recorded).
"""


# Root cause categories for deterministic pre-classification
_ROOT_CAUSE_PATTERNS = {
    "ENVIRONMENT": [
        "ConnectionRefused", "ConnectionError", "socket", "network",
        "timeout", "TimeoutError", "unreachable", "DNS",
    ],
    "TEST_DATA": [
        "FileNotFoundError", "KeyError", "ValueError", "Excel",
        "row not found", "sheet not found", "NoneType",
    ],
    "LOCATOR": [
        "ElementNotFound", "NoSuchElement", "selector", "locator",
        "TimeoutError.*waiting", "strict mode violation",
    ],
    "ASSERTION": [
        "AssertionError", "assert False", "FAILED —",
        "Expected.*but got", "not equal",
    ],
    "AUTHENTICATION": [
        "401", "403", "Unauthorized", "Forbidden",
        "login failed", "session expired", "storageState",
    ],
    "IMPORT": [
        "ImportError", "ModuleNotFoundError", "cannot import",
    ],
    "CONFIGURATION": [
        "config.json", "config not found", "provider", "API key",
    ],
}


class DefectClassifierAgent:
    """
    Classify test failures by root cause and generate actionable defect reports.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def classify(self, execution_results: dict, test_cases: str, rtm: str) -> str:
        """
        Classify test failures and generate defect reports.

        Parameters
        ----------
        execution_results : dict
            Output from TestReportAnalyzerAgent.analyze() — contains
            summary, failed_tests, failure_root_causes, recommendations.
        test_cases : str
            TestGenerator output (TC-XXX-NNN with RTM links).
        rtm : str
            RTMAgent output (for linking failures to requirements).

        Returns
        -------
        str
            Structured defect classification report with root cause analysis,
            defect reports, patterns, and RTM update recommendations.
        """
        # Pre-classify failures deterministically before sending to LLM
        pre_classification = self._pre_classify(execution_results)

        # Format execution results for the prompt
        results_text = self._format_results(execution_results)

        prompt = f"""
You are a Senior QA Engineer and Failure Intelligence Analyst with 15+ years
of experience in defect triage, root cause analysis, and test failure
classification for enterprise applications.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyze the test execution results below and classify every failure by:
  1. Root cause category (PRODUCT_DEFECT vs TEST_DEFECT vs ENVIRONMENT)
  2. Defect type (Functional, Security, Performance, UI, API, Data, Config)
  3. Severity (CRITICAL, HIGH, MEDIUM, LOW)
  4. Affected component
  5. Recommended action (Fix code, Fix test, Fix environment, Investigate)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST EXECUTION RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{results_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRE-CLASSIFICATION (deterministic pattern matching)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{pre_classification}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST CASES (for TC-ID to requirement mapping)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{test_cases[:2000] if len(test_cases) > 2000 else test_cases}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFECT CLASSIFICATION TAXONOMY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Root Cause Category:
  PRODUCT_DEFECT   — The application code has a bug
  TEST_DEFECT      — The test code is wrong (bad assertion, wrong locator, etc.)
  ENVIRONMENT      — Infrastructure issue (network, config, missing data)
  FLAKY_TEST       — Test passes sometimes, fails sometimes (timing/race condition)
  BLOCKED          — Test cannot run due to a dependency failure

Defect Type:
  FUNCTIONAL   — Business logic error
  UI           — UI element not found, wrong text, layout issue
  API          — Wrong status code, wrong response body
  DATA         — Missing test data, wrong data format
  AUTH         — Authentication/authorization failure
  CONFIG       — Missing config, wrong environment setting
  PERFORMANCE  — Timeout, slow response
  REGRESSION   — Previously passing test now fails

Severity:
  CRITICAL — Blocks release, core feature broken
  HIGH     — Important feature broken, workaround exists
  MEDIUM   — Non-critical feature broken
  LOW      — Minor issue, cosmetic

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. EXECUTION SUMMARY

  Total Tests    : [N]
  Passed         : [N] ([X]%)
  Failed         : [N] ([X]%)
  Skipped        : [N]
  Product Defects: [N]
  Test Defects   : [N]
  Environment    : [N]
  Flaky Tests    : [N]

## 2. DEFECT REPORTS (one per failed test)

For each failed test:

─────────────────────────────────────────────────────────────────────────────
DEFECT-[NNN]
  Test Name      : [Full test name]
  TC ID          : [TC-XXX-NNN if mappable, else "Unknown"]
  REQ Link       : [REQ-XXX if mappable, else "Unknown"]
  Root Cause     : [PRODUCT_DEFECT | TEST_DEFECT | ENVIRONMENT | FLAKY_TEST | BLOCKED]
  Defect Type    : [FUNCTIONAL | UI | API | DATA | AUTH | CONFIG | PERFORMANCE | REGRESSION]
  Severity       : [CRITICAL | HIGH | MEDIUM | LOW]
  Component      : [Specific component/module/page affected]
  Error Summary  : [One-line description of the error]
  Root Cause Analysis:
    [2-3 sentences explaining WHY this failure occurred]
  Reproduction Steps:
    1. [Step 1]
    2. [Step 2]
    3. [Expected: X | Actual: Y]
  Recommended Action:
    [FIX_CODE | FIX_TEST | FIX_ENVIRONMENT | INVESTIGATE | MARK_FLAKY]
    [Specific action: what file/line/component to fix]
─────────────────────────────────────────────────────────────────────────────

## 3. FAILURE PATTERN ANALYSIS

Identify patterns across failures:
  - [Pattern description]: Affects [N] tests — [Root cause hypothesis]
  - Example: "3 tests fail with ConnectionError — likely environment issue"

## 4. RTM STATUS UPDATE RECOMMENDATIONS

For each failed test, recommend the RTM status update:
  | TC ID | Current Status | Recommended Status | Defect ID | Notes |
  |-------|---------------|-------------------|-----------|-------|
  | TC-LOGIN-001 | Not Executed | Fail | DEFECT-001 | Product defect in login |

## 5. SPRINT IMPACT ASSESSMENT

  Release Blocker Defects : [N] (CRITICAL product defects)
  Must Fix This Sprint    : [N] (HIGH product defects)
  Test Fixes Required     : [N] (TEST_DEFECT items)
  Environment Fixes       : [N] (ENVIRONMENT items)
  Overall Sprint Health   : [GREEN | AMBER | RED]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Distinguish clearly between product defects and test defects
  - Provide specific reproduction steps for every PRODUCT_DEFECT
  - Identify patterns across multiple failures
  - Link failures to TC-IDs and REQ-IDs where possible

❌ DO NOT:
  - Classify all failures as PRODUCT_DEFECT without evidence
  - Use vague root cause descriptions like "test failed"
  - Skip the pattern analysis
  - Omit the RTM status update recommendations
"""
        return self.llm.generate(prompt)

    def _pre_classify(self, execution_results: dict) -> str:
        """
        Deterministically pre-classify failures using pattern matching.
        This reduces LLM hallucination by providing a starting classification.
        """
        import re
        lines = ["Deterministic pre-classification results:"]
        failed_tests = execution_results.get("failed_tests", [])
        root_causes = execution_results.get("failure_root_causes", [])

        for i, failure in enumerate(root_causes):
            test_name = failure.get("test_name", f"test_{i}")
            log = failure.get("error_snippet", "")
            detected = []

            for category, patterns in _ROOT_CAUSE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, log, re.IGNORECASE):
                        detected.append(category)
                        break

            category_str = detected[0] if detected else "UNKNOWN"
            lines.append(f"  {test_name}: {category_str}")

        return "\n".join(lines) if len(lines) > 1 else "No failures to pre-classify."

    def _format_results(self, execution_results: dict) -> str:
        """Format execution results dict as readable text for the prompt."""
        import json
        # Truncate large log outputs to keep prompt manageable
        results_copy = dict(execution_results)
        for test in results_copy.get("failed_tests", []):
            if "log" in test and len(str(test.get("log", ""))) > 500:
                test["log"] = str(test["log"])[:500] + "... [truncated]"
        return json.dumps(results_copy, indent=2, default=str)

"""
Review Agent
============
Senior QA Lead agent that reviews test case suites against requirement analysis.
Issues formal verdict: APPROVED | APPROVED_WITH_COMMENTS | NEEDS_REVISION | REJECTED
"""


class ReviewAgent:
    """Review a test case suite against requirement analysis and issue a formal verdict."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def review(self, analysis: str, test_cases: str) -> str:
        prompt = f"""
You are a Senior QA Lead and Test Manager with 15+ years of experience,
ISTQB Expert Level certified, responsible for test strategy and quality gates.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Perform a rigorous quality review of the test case suite against the requirement
analysis. Issue a formal verdict and provide a detailed scorecard.

REQUIREMENT ANALYSIS:
{analysis}

TEST CASE SUITE:
{test_cases}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORING (0-10 per dimension):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. RTM COMPLETENESS (25%) — every REQ-XXX has ≥1 test case
2. FUNCTIONAL COVERAGE (20%) — all happy-path scenarios covered
3. NEGATIVE & BOUNDARY COVERAGE (20%) — invalid inputs and edge cases
4. TEST CASE QUALITY (15%) — specific, executable, measurable steps
5. RISK COVERAGE (10%) — high-risk areas have test cases
6. AUTOMATION READINESS (10%) — automation-eligible TCs correctly tagged

REQUIRED OUTPUT SECTIONS:
## 1. REVIEW SCORECARD (table with weighted scores)
## 2. RTM COMPLETENESS CHECK (every REQ-XXX coverage status)
## 3. COVERAGE GAPS (missing scenarios with severity)
## 4. QUALITY ISSUES (specific TC issues with fix recommendations)
## 5. DUPLICATE ANALYSIS
## 6. RISK COVERAGE ASSESSMENT
## 7. AUTOMATION READINESS ASSESSMENT
## 8. IMPROVEMENT ITEMS (prioritized action list)
## 9. FORMAL VERDICT

VERDICT CRITERIA:
  APPROVED              → Overall score ≥ 8.5, no CRITICAL gaps, RTM ≥ 95% covered
  APPROVED_WITH_COMMENTS → Score 7.0–8.4, no CRITICAL gaps
  NEEDS_REVISION        → Score 5.0–6.9, or any HIGH gaps, or RTM < 80%
  REJECTED              → Score < 5.0, or any CRITICAL gaps, or RTM < 60%

OUTPUT RULES:
✅ Check EVERY REQ-XXX from the analysis for test coverage
✅ Score objectively based on evidence
❌ Do NOT issue APPROVED if any CRITICAL gaps exist
❌ Do NOT skip the RTM completeness check
"""
        return self.llm.generate(prompt)

"""
Test Generator Agent
====================
Senior QA Engineer agent that generates comprehensive, traceable test cases
from structured requirement analysis. Produces TC-XXX-NNN IDs with Gherkin steps.
"""


class Generator:
    """Generate a comprehensive, RTM-linked test case suite from requirement analysis."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def generate(self, analysis: str) -> str:
        prompt = f"""
You are a Senior QA Engineer with 12+ years of experience, ISTQB Advanced Level
certified, expert in Equivalence Partitioning, Boundary Value Analysis, Decision
Table Testing, State Transition Testing, and Use Case Testing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate a complete, production-quality test case suite from the requirement
analysis below. Every test case MUST be linked to a REQ-XXX anchor.

TC ID FORMAT: TC-[MODULE]-[NNN]  (e.g. TC-LOGIN-001, TC-USER-001, TC-API-001)

REQUIREMENT ANALYSIS INPUT:
{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATE ALL APPLICABLE CATEGORIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. FUNCTIONAL (Happy Path)
2. NEGATIVE
3. BOUNDARY
4. INTEGRATION
5. SECURITY
6. PERFORMANCE
7. REGRESSION
8. USABILITY / UX

For each test case use EXACTLY this format:

─────────────────────────────────────────────────────────────────────────────
TC ID          : TC-[MODULE]-[NNN]
Title          : [Short descriptive title]
Type           : [FUNCTIONAL|NEGATIVE|BOUNDARY|INTEGRATION|SECURITY|PERFORMANCE|REGRESSION|USABILITY]
Priority       : [P1-CRITICAL|P2-HIGH|P3-MEDIUM|P4-LOW]
RTM Link       : [REQ-XXX, REQ-YYY]  ← MANDATORY
Automation     : [YES|NO|PARTIAL]
Automation Type: [UI_E2E|API|UNIT|INTEGRATION|N/A]

Pre-conditions :
  - [Condition 1]

Steps (Gherkin):
  Given [initial context]
  When  [user action]
  Then  [expected outcome]

Test Data      :
  - [Field]: [Value]

Expected Result: [Precise measurable outcome]
Post-conditions: [System state after execution]
─────────────────────────────────────────────────────────────────────────────

After all test cases, produce a SUMMARY TABLE and COVERAGE METRICS.

OUTPUT RULES:
✅ Use TC-[MODULE]-[NNN] format — always include MODULE abbreviation
✅ Link EVERY test case to at least one REQ-XXX
✅ Write specific Gherkin steps (not vague "Enter data")
❌ Do NOT skip the RTM Link field on any test case
"""
        return self.llm.generate(prompt)

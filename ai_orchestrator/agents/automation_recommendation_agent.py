"""
Automation Recommendation Agent
================================
Test Automation Architect agent that produces evidence-based automation
vs. manual recommendations using a 5-factor decision matrix.

AUTOMATION SCORE = (TS×0.25) + (EF×0.25) + (BC×0.25) + (AC×0.15) + (MC×0.10)
"""


class AutomationRecommendationAgent:
    """Produce evidence-based automation vs. manual recommendations with effort estimates."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def recommend(self, test_cases: str) -> str:
        prompt = f"""
You are a Senior Test Automation Architect with 15+ years of experience building
enterprise automation frameworks using Playwright, pytest, and CI/CD pipelines.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST CASES / KEY SCENARIOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{test_cases}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOMATION DECISION MATRIX (score 1-5 each):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  TS = Test Stability (5=highly stable, 1=very unstable)
  EF = Execution Frequency (5=every commit, 1=quarterly)
  BC = Business Criticality (5=revenue-critical, 1=negligible)
  AC = Automation Complexity INVERSE (5=trivial, 1=very complex)
  MC = Maintenance Cost INVERSE (5=very low, 1=very high)

  AUTOMATION SCORE = (TS×0.25) + (EF×0.25) + (BC×0.25) + (AC×0.15) + (MC×0.10)

  THRESHOLDS:
    Score ≥ 4.0  → AUTOMATE (High Priority)
    Score 3.0–3.9 → AUTOMATE (Medium Priority)
    Score 2.0–2.9 → AUTOMATE (Low Priority / Future Sprint)
    Score < 2.0  → MANUAL ONLY

TOOL REFERENCE:
  UI_E2E      → Playwright + pytest (tests/ui/)
  API         → requests + pytest (tests/api/)
  UNIT        → pytest (tests/)
  INTEGRATION → pytest + requests/Playwright
  HYBRID      → API setup + UI verification

REQUIRED OUTPUT SECTIONS:
## 1. AUTOMATION DECISION MATRIX TABLE
## 2. AUTOMATE — DETAILED RECOMMENDATIONS (with sprint plan, effort, risk if not automated)
## 3. MANUAL ONLY — DETAILED RECOMMENDATIONS (with specific reasons)
## 4. AUTOMATION SPRINT PLAN (Sprint 1/2/3 with effort totals)
## 5. AUTOMATION COVERAGE SUMMARY
## 6. STAKEHOLDER EXECUTIVE SUMMARY

OUTPUT RULES:
✅ Score EVERY scenario using the decision matrix formula
✅ Provide specific justified reasons for every MANUAL ONLY decision
❌ Do NOT recommend automation for CAPTCHA, exploratory, or visual-only tests
❌ Do NOT skip the sprint plan or executive summary
"""
        return self.llm.generate(prompt)

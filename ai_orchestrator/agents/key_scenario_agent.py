"""
Key Scenario Agent
==================
QA Architect agent that identifies highest-value scenarios for automation
with ROI scoring: ROI = (BR×0.4) + (EF×0.35) + (AC×0.25)
"""


class KeyScenarioAgent:
    """Extract and prioritize key automation scenarios with ROI scoring and RTM linkage."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def extract(self, requirement: str, analysis: str) -> str:
        prompt = f"""
You are a Senior QA Architect and Test Strategy Lead with 15+ years of experience
designing enterprise automation frameworks and maximizing automation ROI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Identify the top 5–8 key scenarios that deliver the highest automation ROI.

REQUIREMENT:
{requirement}

REQUIREMENT ANALYSIS (REQ-XXX anchors):
{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROI SCORING: ROI = (BR×0.4) + (EF×0.35) + (AC×0.25) — max 5.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each scenario use EXACTLY this format:

─────────────────────────────────────────────────────────────────────────────
Scenario ID      : KS-[NNN]
Title            : [Short action-oriented title]
Description      : [2-3 sentences]
RTM Link         : [REQ-XXX, REQ-YYY]  ← MANDATORY
Priority         : [P1-CRITICAL | P2-HIGH | P3-MEDIUM | P4-LOW]
Automation Type  : [UI_E2E | API | UNIT | INTEGRATION | HYBRID]
Test Layer       : [UI | API | DATABASE | HYBRID]

ROI Scoring:
  Business Risk (BR)         : [1-5] — [Justification]
  Execution Frequency (EF)   : [1-5] — [Justification]
  Automation Complexity (AC) : [1-5] — [Justification]
  ROI Score                  : [(BR×0.4)+(EF×0.35)+(AC×0.25)]

Framework Components:
  Pages      : [LoginPage | DashboardPage | BasePage | N/A]
  Utilities  : [XLUtils | SessionManager | api_client | N/A]

Effort Estimate:
  Story Points : [1|2|3|5|8|13]
  Hours        : [Estimated hours]

Dependencies    : [KS-XXX must run before this | None]
Execution Order : [NNN]
─────────────────────────────────────────────────────────────────────────────

After all scenarios, produce a ranked summary table and AUTOMATION SPRINT PLAN.

OUTPUT RULES:
✅ Calculate ROI using the formula
✅ Link EVERY scenario to at least one REQ-XXX
✅ Rank scenarios by ROI score (highest first)
❌ Do NOT recommend automation for inherently manual scenarios
"""
        return self.llm.generate(prompt)

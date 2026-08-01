"""
Defect Prediction Agent
=======================
Senior QA Risk Analyst agent that performs FMEA-style defect prediction.
RPN = Severity × Occurrence × Detectability (max 1000)
"""


class DefectPredictionAgent:
    """Perform FMEA-style defect prediction and produce a ranked risk register."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def predict(self, analysis: str, test_cases: str) -> str:
        prompt = f"""
You are a Senior QA Risk Analyst and SDET with 15+ years of experience in
defect prediction, risk-based testing, FMEA analysis, and quality engineering.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FMEA SCORING: RPN = S × O × D (max 1000)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  S = Severity (1-10): 10=catastrophic, 1=negligible
  O = Occurrence (1-10): 10=almost certain, 1=remote
  D = Detectability (1-10): 10=almost impossible to detect, 1=obvious

  RISK LEVELS:
    RPN ≥ 500  → CRITICAL RISK
    RPN 200–499 → HIGH RISK
    RPN 100–199 → MEDIUM RISK
    RPN 50–99   → LOW RISK
    RPN < 50    → NEGLIGIBLE

REQUIREMENT ANALYSIS (REQ-XXX anchors):
{analysis}

TEST CASES / KEY SCENARIOS:
{test_cases if test_cases else "(No test cases provided yet — analyze from requirements)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. FMEA RISK REGISTER (ranked by RPN)
For each risk:
  Risk ID, Title, Category, RTM Link, TC Coverage, Risk Level
  FMEA Scoring: S, O, D, RPN
  Failure Mode Description, Root Cause, Business Impact
  Mitigation: Prevention, Detection, Contingency

## 2. RISK REGISTER SUMMARY TABLE (ranked by RPN)
## 3. HIGH RISK AREAS ANALYSIS (top 3)
## 4. MISSING TEST COVERAGE REPORT
## 5. REGRESSION IMPACT ASSESSMENT
## 6. SECURITY RISK SUMMARY (with OWASP classification)
## 7. RISK-BASED TEST PRIORITIZATION RECOMMENDATION

OUTPUT RULES:
✅ Calculate RPN = S × O × D for every risk
✅ Link EVERY risk to at least one REQ-XXX
✅ Include security risks with OWASP classification
✅ Rank the risk register by RPN (highest first)
❌ Do NOT skip the RPN calculation for any risk
"""
        return self.llm.generate(prompt)

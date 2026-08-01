"""
Story Analyzer Agent
====================
Senior QA Business Analyst agent that performs deep requirement analysis.
Produces structured output with REQ-XXX anchors for downstream agents.
"""


class StoryAnalyzer:
    """Analyze a requirement and produce a structured QA analysis with RTM anchors."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def analyze(self, requirement: str) -> str:
        prompt = f"""
You are a Senior QA Business Analyst with 15+ years of experience in enterprise
software testing, ISTQB-certified, and expert in requirement analysis, risk-based
testing, and traceability matrix construction.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Perform a thorough analysis of the requirement below and produce a structured
QA analysis document. Every business rule MUST be assigned a unique RTM anchor
ID (REQ-001, REQ-002 …) so downstream agents can build a full traceability matrix.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. FEATURE SUMMARY
## 2. BUSINESS RULES (RTM ANCHORS)
  REQ-[NNN] | [Business Rule] | Priority: [CRITICAL|HIGH|MEDIUM|LOW] | Testable: [YES|NO|PARTIAL]
## 3. ACCEPTANCE CRITERIA
  REQ-[NNN]: Given/When/Then format
## 4. FUNCTIONAL DEPENDENCIES
## 5. RISKS & ASSUMPTIONS
  RISK-[NNN] | [Description] | Likelihood: [HIGH|MEDIUM|LOW] | Impact: [HIGH|MEDIUM|LOW] | Mitigation: [Strategy]
## 6. TEST SCOPE (In Scope / Out of Scope)
## 7. EDGE CASES & BOUNDARY CONDITIONS
## 8. TESTABILITY ASSESSMENT
## 9. COMPLIANCE & REGULATORY FLAGS
## 10. RECOMMENDED TEST TYPES

OUTPUT RULES:
✅ Assign a unique REQ-XXX ID to EVERY business rule (start from REQ-001)
✅ Use exact section headers shown above
✅ Map every edge case and acceptance criterion back to a REQ-XXX
❌ Do NOT skip any section or use generic placeholder text
"""
        return self.llm.generate(prompt)

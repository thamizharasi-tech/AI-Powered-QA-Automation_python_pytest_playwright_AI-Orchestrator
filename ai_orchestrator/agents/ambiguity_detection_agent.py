"""
Ambiguity Analyzer Agent
========================
Agile QA Lead agent that detects unclear, incomplete, or contradictory
requirements BEFORE any test generation begins.

Responsibilities:
  - Identify ambiguous, vague, or missing acceptance criteria
  - Detect contradictions between requirements
  - Flag untestable requirements
  - Identify missing information that would block test design
  - Return a structured NEEDS_CLARIFICATION response with specific questions
    OR a CLEAR status allowing the pipeline to proceed

Pipeline Position:
  Runs AFTER StoryAnalyzer, BEFORE KeyScenarioAgent.
  If status == NEEDS_CLARIFICATION, the pipeline PAUSES and surfaces
  the questions to the human before continuing.

Architectural Principle:
  AI DECIDES / RECOMMENDS — the LLM identifies ambiguities
  HUMAN APPROVES — a human must answer the questions before proceeding
  The framework never silently invents missing requirements.
"""


class AmbiguityAnalyzer:
    """
    Detect requirement ambiguities and return structured clarification requests.

    Returns either:
      - status: CLEAR          → pipeline may proceed
      - status: NEEDS_CLARIFICATION → pipeline pauses, questions surfaced to human
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def analyze(self, requirement: str, analysis: str) -> str:
        """
        Analyze the requirement and StoryAnalyzer output for ambiguities.

        Parameters
        ----------
        requirement : str
            Original raw requirement text.
        analysis : str
            Structured analysis from StoryAnalyzer (REQ-XXX anchors).

        Returns
        -------
        str
            Structured ambiguity report. Contains status CLEAR or
            NEEDS_CLARIFICATION with specific questions.
        """
        prompt = f"""
You are a Senior QA Lead and Business Analyst with 15+ years of experience
in Agile/Scrum projects. You are the quality gate between raw requirements
and test design. Your job is to catch ambiguities BEFORE they become
defective test cases or missed coverage.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyze the requirement and its structured analysis for:
  1. Ambiguous or vague statements that could be interpreted multiple ways
  2. Missing acceptance criteria (what does "success" look like?)
  3. Contradictions between requirements
  4. Untestable requirements (no measurable outcome)
  5. Missing preconditions or dependencies
  6. Undefined error handling or edge case behavior
  7. Missing non-functional requirements (performance, security, accessibility)
  8. Scope creep indicators (requirements that imply hidden features)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURED ANALYSIS (from StoryAnalyzer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AMBIGUITY CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Classify each ambiguity by type:
  VAGUE          — Statement is too general to write a specific test case
  MISSING        — Required information is absent (no acceptance criteria, no error behavior)
  CONTRADICTORY  — Two requirements conflict with each other
  UNTESTABLE     — No measurable or observable outcome defined
  ASSUMPTION     — Requirement relies on an unstated assumption
  SCOPE_UNCLEAR  — Boundary of the feature is not defined

Classify each ambiguity by severity:
  BLOCKER  — Cannot write any test cases without clarification
  CRITICAL — Will cause significant coverage gaps if not clarified
  MAJOR    — Will cause some coverage gaps
  MINOR    — Can proceed with reasonable assumption, but should be confirmed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## AMBIGUITY ANALYSIS REPORT

### STATUS: [CLEAR | NEEDS_CLARIFICATION]

(Use CLEAR only if there are ZERO BLOCKER or CRITICAL ambiguities.
 Use NEEDS_CLARIFICATION if ANY BLOCKER or CRITICAL ambiguity exists.)

### AMBIGUITIES FOUND: [N]

For each ambiguity found:

─────────────────────────────────────────────────────────────────────────────
AMBIGUITY-[NNN]
  Type        : [VAGUE | MISSING | CONTRADICTORY | UNTESTABLE | ASSUMPTION | SCOPE_UNCLEAR]
  Severity    : [BLOCKER | CRITICAL | MAJOR | MINOR]
  Requirement : [REQ-XXX or "General"]
  Description : [Specific description of the ambiguity]
  Impact      : [What test coverage gap this creates if not clarified]
  Question    : [Specific, answerable question for the Product Owner / BA]
  Assumption  : [If MINOR — what assumption can be made to proceed]
─────────────────────────────────────────────────────────────────────────────

### CLARIFICATION QUESTIONS (for Product Owner)

If status is NEEDS_CLARIFICATION, list all BLOCKER and CRITICAL questions
in priority order:

  Q1. [Question] — Affects: [REQ-XXX] — Severity: BLOCKER
  Q2. [Question] — Affects: [REQ-XXX] — Severity: CRITICAL
  ...

### PIPELINE DECISION

  Status          : [CLEAR | NEEDS_CLARIFICATION]
  Blocker Count   : [N]
  Critical Count  : [N]
  Major Count     : [N]
  Minor Count     : [N]
  Recommendation  : [PROCEED | PAUSE_FOR_CLARIFICATION]

  If PROCEED:
    "All requirements are sufficiently clear to begin test design.
     [N] minor assumptions documented above."

  If PAUSE_FOR_CLARIFICATION:
    "Pipeline paused. [N] questions must be answered before test design
     can begin. Unresolved ambiguities will cause coverage gaps."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Be specific about WHAT is ambiguous and WHY it matters for testing
  - Write questions that a Product Owner can actually answer
  - Link every ambiguity to a REQ-XXX from the analysis
  - Distinguish between "cannot proceed" (BLOCKER) and "can assume" (MINOR)

❌ DO NOT:
  - Invent requirements to fill gaps — flag them instead
  - Mark a requirement CLEAR if any BLOCKER ambiguity exists
  - Ask vague questions like "please clarify the requirements"
  - Skip the Pipeline Decision section
"""
        return self.llm.generate(prompt)

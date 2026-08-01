"""
Sprint QA Summary Agent
=======================
QA Manager / Scrum Master agent that generates a comprehensive Sprint QA
Summary at the end of the pipeline, suitable for sprint review meetings,
stakeholder reporting, and release decisions.

Responsibilities:
  - Aggregate all pipeline outputs into a sprint-level summary
  - Calculate sprint QA health metrics
  - Identify release readiness
  - Highlight risks and blockers
  - Provide go/no-go recommendation for release
  - Generate stakeholder-ready executive summary
  - Produce sprint retrospective data points

Pipeline Position:
  Runs as the FINAL step in the pipeline, after all other agents.
  Consumes outputs from: StoryAnalyzer, TestGenerator, ReviewAgent,
  AutomationAgent, DefectClassifierAgent, RTMAgent.

Architectural Principle:
  AI SYNTHESIZES all pipeline outputs into a coherent sprint narrative.
  The summary is informational — HUMAN makes the final release decision.
"""


class SprintSummaryAgent:
    """
    Generate a comprehensive Sprint QA Summary from all pipeline outputs.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def summarize(
        self,
        requirement: str,
        analysis: str,
        ambiguity_report: str,
        impact_report: str,
        test_cases: str,
        review: str,
        recommendation: str,
        reuse_report: str,
        defect_prediction: str,
        rtm: str,
        execution_results: str = "",
        defect_classification: str = "",
    ) -> str:
        """
        Generate the Sprint QA Summary.

        Parameters
        ----------
        requirement : str
            Original requirement text.
        analysis : str
            StoryAnalyzer output.
        ambiguity_report : str
            AmbiguityAnalyzer output.
        impact_report : str
            ImpactAnalyzer output.
        test_cases : str
            TestGenerator output.
        review : str
            ReviewAgent output (test case review verdict).
        recommendation : str
            AutomationRecommendationAgent output.
        reuse_report : str
            FrameworkReuseAgent output.
        defect_prediction : str
            DefectPredictionAgent output (FMEA).
        rtm : str
            RTMAgent output (compliance score).
        execution_results : str
            TestReportAnalyzerAgent output (optional — if tests were run).
        defect_classification : str
            DefectClassifierAgent output (optional — if tests were run).

        Returns
        -------
        str
            Comprehensive Sprint QA Summary with metrics, health indicators,
            release readiness assessment, and executive summary.
        """
        # Build execution section only if results are available
        execution_section = ""
        if execution_results:
            execution_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST EXECUTION RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{execution_results}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFECT CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{defect_classification}
"""

        prompt = f"""
You are a Senior QA Manager and Scrum Master with 15+ years of experience
in Agile/Scrum quality management, sprint reporting, and release governance.
You are responsible for the Sprint QA Summary presented at sprint review.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Synthesize all pipeline outputs into a comprehensive Sprint QA Summary.
This document will be presented at the sprint review meeting and used
to make the release go/no-go decision.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT ANALYSIS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis[:1500] if len(analysis) > 1500 else analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AMBIGUITY STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{ambiguity_report[:800] if len(ambiguity_report) > 800 else ambiguity_report}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPACT ANALYSIS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{impact_report[:800] if len(impact_report) > 800 else impact_report}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST CASE REVIEW VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{review[:1000] if len(review) > 1000 else review}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOMATION RECOMMENDATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{recommendation[:800] if len(recommendation) > 800 else recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFECT PREDICTION (FMEA) SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{defect_prediction[:800] if len(defect_prediction) > 800 else defect_prediction}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RTM COMPLIANCE SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{rtm[:800] if len(rtm) > 800 else rtm}

{execution_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. SPRINT QA HEALTH DASHBOARD

  ┌─────────────────────────────────────────────────────────────────────┐
  │                    SPRINT QA HEALTH DASHBOARD                       │
  ├─────────────────────────────────────────────────────────────────────┤
  │  Sprint Health          : [🟢 GREEN | 🟡 AMBER | 🔴 RED]           │
  │  Requirements Analyzed  : [N]                                       │
  │  Ambiguity Status       : [CLEAR | NEEDS_CLARIFICATION]             │
  │  Test Cases Generated   : [N]                                       │
  │  Test Review Verdict    : [APPROVED | APPROVED_WITH_COMMENTS | ...]  │
  │  RTM Compliance Score   : [X]/100                                   │
  │  Automation Coverage    : [X]%                                      │
  │  Critical Risks (FMEA)  : [N]                                       │
  │  Tests Executed         : [N] (if available)                        │
  │  Pass Rate              : [X]% (if available)                       │
  │  Open Defects           : [N] (if available)                        │
  └─────────────────────────────────────────────────────────────────────┘

## 2. SPRINT QA METRICS

  | Metric | Value | Target | Status |
  |--------|-------|--------|--------|
  | Requirements Coverage | [X]% | ≥ 95% | [✅/⚠️/❌] |
  | Test Case Quality Score | [X]/10 | ≥ 8.0 | [✅/⚠️/❌] |
  | Automation Coverage | [X]% | ≥ 70% | [✅/⚠️/❌] |
  | RTM Compliance Score | [X]/100 | ≥ 85 | [✅/⚠️/❌] |
  | Critical Risk Count | [N] | 0 | [✅/⚠️/❌] |
  | Pass Rate (if run) | [X]% | ≥ 80% | [✅/⚠️/❌] |

## 3. KEY ACHIEVEMENTS THIS SPRINT

  ✅ [Achievement 1 — specific and measurable]
  ✅ [Achievement 2]
  ✅ [Achievement 3]

## 4. RISKS & BLOCKERS

  🔴 BLOCKER: [Description] — Owner: [Team/Person] — Action: [Required action]
  🟡 RISK: [Description] — Mitigation: [Strategy]
  🟡 RISK: [Description] — Mitigation: [Strategy]

## 5. RELEASE READINESS ASSESSMENT

  ┌─────────────────────────────────────────────────────────────────────┐
  │  RELEASE RECOMMENDATION: [GO | CONDITIONAL_GO | NO_GO]             │
  └─────────────────────────────────────────────────────────────────────┘

  GO              → All quality gates passed, no critical defects
  CONDITIONAL_GO  → Minor issues exist, acceptable with documented risk
  NO_GO           → Critical defects or coverage gaps block release

  Justification:
  [3-4 sentences explaining the release recommendation with evidence]

  Conditions for GO (if CONDITIONAL_GO):
  [List specific conditions that must be met]

## 6. PIPELINE ARTIFACTS GENERATED

  ✅ Requirement Analysis    — [N] REQ-XXX anchors
  ✅ Ambiguity Report        — Status: [CLEAR/NEEDS_CLARIFICATION]
  ✅ Impact Analysis         — [N] impact areas identified
  ✅ Test Cases              — [N] TC-XXX-NNN generated
  ✅ Test Review             — Verdict: [APPROVED/...]
  ✅ Automation Scripts      — [N] scripts saved to tests/
  ✅ Test Data               — Written to testData/API_testData.xlsx
  ✅ Defect Predictions      — [N] risks, [N] critical
  ✅ RTM                     — Compliance score: [X]/100
  [✅/⏭] Test Execution     — [N] tests run, [X]% pass rate (if available)
  [✅/⏭] Defect Reports     — [N] defects classified (if available)

## 7. EXECUTIVE SUMMARY (for Sprint Review Meeting)

  [5-6 sentences suitable for a non-technical stakeholder audience:
   - What was the feature/requirement tested this sprint
   - How many test cases were created and what coverage was achieved
   - What automation was built and what ROI it provides
   - What risks were identified and how they are being mitigated
   - Whether the feature is ready for release
   - What the team should focus on next sprint]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Use specific numbers from the pipeline outputs (not estimates)
  - Make the release recommendation clear and justified
  - Write the executive summary for a non-technical audience
  - Highlight both achievements and risks

❌ DO NOT:
  - Recommend GO if any critical defects or BLOCKER ambiguities exist
  - Use technical jargon in the executive summary
  - Skip the release readiness assessment
  - Omit the pipeline artifacts section
"""
        return self.llm.generate(prompt)

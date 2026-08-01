"""
Retrospective Agent
===================
Agile Coach / QA Process Improvement agent that generates continuous
improvement insights and retrospective data points from the completed
pipeline run.

Responsibilities:
  - Identify what went well in the QA process this sprint
  - Identify what could be improved
  - Detect recurring patterns across pipeline runs
  - Recommend process improvements for the next sprint
  - Identify automation debt and technical debt
  - Suggest framework enhancements based on observed gaps
  - Generate actionable improvement items for the team

Pipeline Position:
  Runs AFTER SprintSummaryAgent as the absolute last step.
  Output is informational — feeds into team retrospective meetings.

Architectural Principle:
  AI IDENTIFIES improvement opportunities from pipeline data.
  HUMAN DECIDES which improvements to implement.
  The framework works without this agent.
"""


class RetrospectiveAgent:
    """
    Generate continuous improvement insights from the completed pipeline run.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def generate_insights(
        self,
        sprint_summary: str,
        ambiguity_report: str,
        review_verdict: str,
        automation_review: str,
        defect_classification: str = "",
        previous_retrospective: str = "",
    ) -> str:
        """
        Generate retrospective insights and improvement recommendations.

        Parameters
        ----------
        sprint_summary : str
            SprintSummaryAgent output.
        ambiguity_report : str
            AmbiguityAnalyzer output (were requirements clear?).
        review_verdict : str
            ReviewAgent output (test case quality verdict).
        automation_review : str
            AutomationReviewAgent output (code quality verdict).
        defect_classification : str
            DefectClassifierAgent output (optional).
        previous_retrospective : str
            Previous sprint's retrospective (optional — for trend analysis).

        Returns
        -------
        str
            Structured retrospective report with improvement items,
            trend analysis, and next sprint recommendations.
        """
        previous_section = ""
        if previous_retrospective:
            previous_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREVIOUS SPRINT RETROSPECTIVE (for trend analysis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{previous_retrospective[:1000]}
"""

        defect_section = ""
        if defect_classification:
            defect_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFECT CLASSIFICATION (for process improvement)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{defect_classification[:800]}
"""

        prompt = f"""
You are an experienced Agile Coach and QA Process Improvement Specialist
with 15+ years of experience facilitating retrospectives, identifying
process improvements, and building high-performing QA teams.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyze the completed pipeline run and generate actionable retrospective
insights. Focus on process improvements that will make the NEXT sprint
more efficient, higher quality, and less risky.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPRINT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{sprint_summary[:1500] if len(sprint_summary) > 1500 else sprint_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT AMBIGUITY REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{ambiguity_report[:600] if len(ambiguity_report) > 600 else ambiguity_report}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST CASE REVIEW VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{review_verdict[:600] if len(review_verdict) > 600 else review_verdict}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOMATION CODE REVIEW VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{automation_review[:600] if len(automation_review) > 600 else automation_review}

{defect_section}
{previous_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. WHAT WENT WELL ✅

List specific things that worked well this sprint:
  ✅ [Specific achievement with evidence from pipeline data]
  ✅ [Specific achievement]
  ✅ [Specific achievement]

## 2. WHAT COULD BE IMPROVED ⚠️

List specific areas for improvement:
  ⚠️ [Specific issue] — Evidence: [Data point from pipeline] — Impact: [Effect on quality]
  ⚠️ [Specific issue] — Evidence: [Data point] — Impact: [Effect]

## 3. IMPROVEMENT ACTION ITEMS

For each improvement, provide a concrete action item:

─────────────────────────────────────────────────────────────────────────────
ACTION-[NNN]
  Category    : [PROCESS | FRAMEWORK | REQUIREMENTS | AUTOMATION | TESTING | TOOLING]
  Priority    : [HIGH | MEDIUM | LOW]
  Title       : [Short action title]
  Description : [What specifically should be done]
  Owner       : [QA Lead | Dev Team | BA | Product Owner | DevOps]
  Sprint      : [Next Sprint | Sprint+2 | Backlog]
  Expected Benefit: [What improvement this will deliver]
─────────────────────────────────────────────────────────────────────────────

## 4. AUTOMATION DEBT REGISTER

List automation gaps that should be addressed:
  | Gap | Priority | Effort | Business Value | Recommended Sprint |
  |-----|----------|--------|----------------|-------------------|
  | [Missing test for X] | HIGH | 3h | Prevents regression | Next Sprint |

## 5. FRAMEWORK ENHANCEMENT SUGGESTIONS

Based on this sprint's experience, suggest framework improvements:
  - [Enhancement]: [What to add/change in the framework and why]
  - [Enhancement]: [What to add/change and why]

## 6. TREND ANALYSIS (if previous retrospective available)

  Improving: [Areas that are getting better sprint over sprint]
  Declining: [Areas that are getting worse — needs attention]
  Stable:    [Areas that are consistent]

## 7. NEXT SPRINT RECOMMENDATIONS

Top 3 priorities for the next sprint's QA activities:
  1. [Priority 1] — Reason: [Why this is most important]
  2. [Priority 2] — Reason: [Why this is second priority]
  3. [Priority 3] — Reason: [Why this is third priority]

## 8. TEAM RECOGNITION

  🏆 [Specific positive callout about what the team did well]
  💡 [Learning or insight the team should carry forward]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  - Base every observation on specific evidence from the pipeline data
  - Make action items specific, measurable, and assignable
  - Balance positive recognition with constructive improvement
  - Focus on process improvements, not blame

❌ DO NOT:
  - Make vague suggestions like "improve test quality"
  - Skip the action items section
  - Assign all actions to the same owner
  - Ignore positive achievements
"""
        return self.llm.generate(prompt)

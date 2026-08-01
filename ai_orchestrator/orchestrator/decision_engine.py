"""
Decision Engine
===============
Deterministic rule engine that makes pipeline flow decisions based on
agent outputs. The LLM recommends; the Decision Engine validates and decides.

Architectural Principle:
  AI DECIDES / RECOMMENDS — agents produce outputs
  CODE VALIDATES — this engine applies deterministic rules
  HUMAN APPROVES — critical decisions are surfaced for human review

The Decision Engine NEVER calls the LLM. It applies pure Python logic
to structured data extracted from agent outputs.

Usage:
    from ai_orchestrator.orchestrator.decision_engine import DecisionEngine
    from ai_orchestrator.schemas.pipeline_schemas import PipelineContext

    engine = DecisionEngine()
    decision = engine.should_proceed_after_ambiguity(context)
    if not decision.proceed:
        print(decision.reason)
        pipeline.pause()
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from ai_orchestrator.schemas.pipeline_schemas import (
    AmbiguityStatus,
    AutomationVerdict,
    ClarificationRequest,
    PipelineContext,
    ReleaseRecommendation,
    ReviewVerdict,
    RTMMetrics,
    TestCaseMetrics,
)


@dataclass
class Decision:
    """Result of a decision engine evaluation."""
    proceed: bool
    reason: str
    warnings: List[str]
    action_required: Optional[str] = None

    def __bool__(self) -> bool:
        return self.proceed


class DecisionEngine:
    """
    Applies deterministic rules to pipeline context to make flow decisions.

    All methods return a Decision object with:
      - proceed: bool — whether the pipeline should continue
      - reason: str — explanation of the decision
      - warnings: list — non-blocking issues to surface
      - action_required: str — what the human must do if proceed=False
    """

    # Quality thresholds (deterministic — not LLM-dependent)
    MIN_TEST_CASES_FOR_PROCEED = 3
    MIN_RTM_COMPLIANCE_SCORE   = 50   # Below this → flag but don't block
    WARN_RTM_COMPLIANCE_SCORE  = 70   # Below this → warn
    MIN_AUTOMATION_PERCENTAGE  = 30   # Below this → warn
    MAX_CODE_REVIEW_RETRIES    = 2    # Max times to retry AutomationAgent

    def should_proceed_after_ambiguity(
        self, context: PipelineContext
    ) -> Decision:
        """
        Decide whether to proceed after AmbiguityAnalyzer runs.

        Rule: PROCEED only if status == CLEAR.
        If NEEDS_CLARIFICATION, surface questions to human and PAUSE.
        """
        clarification = ClarificationRequest.from_text(context.ambiguity_report)
        context.ambiguity_status = clarification.status

        if clarification.status == AmbiguityStatus.CLEAR:
            return Decision(
                proceed=True,
                reason="Requirements are clear. No blockers or critical ambiguities found.",
                warnings=[],
            )

        questions_text = "\n".join(
            f"  Q{i+1}. {q}" for i, q in enumerate(clarification.questions[:5])
        )
        return Decision(
            proceed=False,
            reason=(
                f"Requirements have {clarification.blocker_count} BLOCKER and "
                f"{clarification.critical_count} CRITICAL ambiguities. "
                "Pipeline paused pending clarification."
            ),
            warnings=[],
            action_required=(
                f"Please answer the following questions before proceeding:\n"
                f"{questions_text}\n"
                f"  (See full ambiguity report for all questions)"
            ),
        )

    def should_proceed_after_review(
        self, context: PipelineContext
    ) -> Decision:
        """
        Decide whether to proceed after ReviewAgent (test case review).

        Rule:
          APPROVED or APPROVED_WITH_COMMENTS → PROCEED (with warnings if comments)
          NEEDS_REVISION or REJECTED → WARN but still proceed
            (human can override; pipeline doesn't hard-block on test case quality)
        """
        verdict = ReviewVerdict.from_text(context.review)
        context.review_verdict = verdict
        warnings = []

        if verdict == ReviewVerdict.APPROVED:
            return Decision(
                proceed=True,
                reason="Test case review APPROVED. All quality gates passed.",
                warnings=[],
            )

        if verdict == ReviewVerdict.APPROVED_WITH_COMMENTS:
            warnings.append(
                "Test case review APPROVED_WITH_COMMENTS. "
                "Minor improvements recommended — review the review report."
            )
            return Decision(
                proceed=True,
                reason="Test case review APPROVED_WITH_COMMENTS. Proceeding with warnings.",
                warnings=warnings,
            )

        if verdict == ReviewVerdict.NEEDS_REVISION:
            warnings.append(
                "⚠️  Test case review verdict: NEEDS_REVISION. "
                "Coverage gaps or quality issues detected. "
                "Proceeding but human review of test cases is strongly recommended."
            )
            return Decision(
                proceed=True,  # Don't hard-block — human can override
                reason="Test case review NEEDS_REVISION. Proceeding with warnings.",
                warnings=warnings,
                action_required="Review the test case review report and address gaps before execution.",
            )

        # REJECTED
        warnings.append(
            "🔴 Test case review verdict: REJECTED. "
            "Critical coverage gaps detected. "
            "Proceeding but test execution results may be unreliable."
        )
        return Decision(
            proceed=True,  # Don't hard-block — human can override
            reason="Test case review REJECTED. Proceeding with critical warnings.",
            warnings=warnings,
            action_required="CRITICAL: Address all rejected test cases before execution.",
        )

    def should_proceed_after_automation_review(
        self, context: PipelineContext, retry_count: int = 0
    ) -> Decision:
        """
        Decide whether to proceed after AutomationReviewAgent (code review).

        Rule:
          APPROVED → PROCEED
          NEEDS_REVISION + retries remaining → RETRY AutomationAgent
          NEEDS_REVISION + no retries left → PROCEED with warning
        """
        verdict = AutomationVerdict.from_text(context.automation_review)
        context.automation_verdict = verdict

        if verdict == AutomationVerdict.APPROVED:
            return Decision(
                proceed=True,
                reason="Automation code review APPROVED.",
                warnings=[],
            )

        if retry_count < self.MAX_CODE_REVIEW_RETRIES:
            return Decision(
                proceed=False,
                reason=(
                    f"Automation code review NEEDS_REVISION "
                    f"(retry {retry_count + 1}/{self.MAX_CODE_REVIEW_RETRIES})."
                ),
                warnings=[],
                action_required="AutomationAgent will be re-run with review feedback.",
            )

        # Max retries exhausted
        return Decision(
            proceed=True,
            reason="Automation code review NEEDS_REVISION but max retries exhausted. Proceeding.",
            warnings=[
                "⚠️  Generated code has unresolved review issues. "
                "Manual code review recommended before committing to test suite."
            ],
        )

    def validate_test_case_count(self, context: PipelineContext) -> Decision:
        """
        Validate that a minimum number of test cases were generated.
        """
        metrics = TestCaseMetrics.from_text(context.test_cases)
        warnings = []

        if metrics.total_count == 0:
            return Decision(
                proceed=False,
                reason="No test cases were generated. Cannot proceed.",
                warnings=[],
                action_required="Check the TestGenerator output and retry.",
            )

        if metrics.total_count < self.MIN_TEST_CASES_FOR_PROCEED:
            warnings.append(
                f"Only {metrics.total_count} test case(s) generated. "
                f"Expected at least {self.MIN_TEST_CASES_FOR_PROCEED}."
            )

        if metrics.automation_eligible == 0:
            warnings.append(
                "No test cases marked as automation-eligible. "
                "AutomationAgent will have nothing to generate."
            )

        return Decision(
            proceed=True,
            reason=f"{metrics.total_count} test cases generated successfully.",
            warnings=warnings,
        )

    def validate_rtm_compliance(self, context: PipelineContext) -> Decision:
        """
        Validate RTM compliance score and surface warnings.
        """
        metrics = RTMMetrics.from_text(context.rtm)
        warnings = []

        if metrics.compliance_score < self.MIN_RTM_COMPLIANCE_SCORE:
            warnings.append(
                f"🔴 RTM compliance score {metrics.compliance_score}/100 is below "
                f"minimum threshold of {self.MIN_RTM_COMPLIANCE_SCORE}. "
                "Significant coverage gaps exist."
            )
        elif metrics.compliance_score < self.WARN_RTM_COMPLIANCE_SCORE:
            warnings.append(
                f"⚠️  RTM compliance score {metrics.compliance_score}/100 is below "
                f"recommended threshold of {self.WARN_RTM_COMPLIANCE_SCORE}."
            )

        if metrics.automation_percentage < self.MIN_AUTOMATION_PERCENTAGE:
            warnings.append(
                f"⚠️  Automation coverage {metrics.automation_percentage:.1f}% is below "
                f"recommended {self.MIN_AUTOMATION_PERCENTAGE}%."
            )

        return Decision(
            proceed=True,
            reason=f"RTM compliance score: {metrics.compliance_score}/100.",
            warnings=warnings,
        )

    def assess_release_readiness(self, context: PipelineContext) -> Decision:
        """
        Make a final release readiness assessment based on all pipeline outputs.
        This is a deterministic check that complements SprintSummaryAgent's LLM output.
        """
        warnings = []
        blockers = []

        # Check ambiguity status
        if context.ambiguity_status == AmbiguityStatus.NEEDS_CLARIFICATION:
            blockers.append("Unresolved requirement ambiguities exist.")

        # Check review verdict
        if context.review_verdict == ReviewVerdict.REJECTED:
            blockers.append("Test case review was REJECTED.")

        # Check RTM compliance
        rtm_metrics = RTMMetrics.from_text(context.rtm)
        if rtm_metrics.compliance_score < self.MIN_RTM_COMPLIANCE_SCORE:
            blockers.append(
                f"RTM compliance score {rtm_metrics.compliance_score}/100 is critically low."
            )

        # Check for errors in pipeline
        if context.errors:
            warnings.append(f"{len(context.errors)} pipeline error(s) occurred.")

        # Determine recommendation
        if blockers:
            context.release_recommendation = ReleaseRecommendation.NO_GO
            return Decision(
                proceed=False,
                reason=f"NO_GO: {len(blockers)} release blocker(s) found.",
                warnings=warnings,
                action_required="\n".join(f"  🔴 {b}" for b in blockers),
            )

        if warnings:
            context.release_recommendation = ReleaseRecommendation.CONDITIONAL_GO
            return Decision(
                proceed=True,
                reason="CONDITIONAL_GO: Release possible with documented risks.",
                warnings=warnings,
            )

        context.release_recommendation = ReleaseRecommendation.GO
        return Decision(
            proceed=True,
            reason="GO: All quality gates passed.",
            warnings=[],
        )

    def extract_ambiguity_questions(self, ambiguity_report: str) -> List[str]:
        """Extract clarification questions from AmbiguityAnalyzer output."""
        questions = re.findall(
            r'Q\d+\.\s+(.+?)(?:\s+—\s+Affects:|$)', ambiguity_report, re.MULTILINE
        )
        return [q.strip() for q in questions if q.strip()]

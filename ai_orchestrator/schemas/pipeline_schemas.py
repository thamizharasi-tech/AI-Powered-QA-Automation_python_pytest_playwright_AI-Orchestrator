"""
Pipeline Schemas
================
Pydantic models for validating structured data flowing between pipeline stages.

These schemas enforce the contract between agents:
  - AmbiguityAnalyzer must return a status of CLEAR or NEEDS_CLARIFICATION
  - ReviewAgent must return one of the 4 valid verdicts
  - AutomationReviewAgent must return APPROVED or NEEDS_REVISION
  - SprintSummaryAgent must return GO, CONDITIONAL_GO, or NO_GO

Usage:
    from ai_orchestrator.schemas.pipeline_schemas import (
        AmbiguityStatus, ReviewVerdict, AutomationVerdict, ReleaseRecommendation
    )

    status = AmbiguityStatus.from_text(agent_output)
    if status == AmbiguityStatus.NEEDS_CLARIFICATION:
        pipeline.pause()

Note: These are lightweight dataclasses/enums that work WITHOUT pydantic
installed. If pydantic is available, richer validation is used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations — valid values for key pipeline decisions
# ─────────────────────────────────────────────────────────────────────────────

class AmbiguityStatus(str, Enum):
    """Status returned by AmbiguityAnalyzer."""
    CLEAR                 = "CLEAR"
    NEEDS_CLARIFICATION   = "NEEDS_CLARIFICATION"

    @classmethod
    def from_text(cls, text: str) -> "AmbiguityStatus":
        """Extract status from agent output text."""
        if "NEEDS_CLARIFICATION" in text.upper():
            return cls.NEEDS_CLARIFICATION
        if "CLEAR" in text.upper():
            return cls.CLEAR
        # Default to NEEDS_CLARIFICATION if status cannot be determined
        return cls.NEEDS_CLARIFICATION


class ReviewVerdict(str, Enum):
    """Verdict returned by ReviewAgent (test case review)."""
    APPROVED              = "APPROVED"
    APPROVED_WITH_COMMENTS = "APPROVED_WITH_COMMENTS"
    NEEDS_REVISION        = "NEEDS_REVISION"
    REJECTED              = "REJECTED"

    @classmethod
    def from_text(cls, text: str) -> "ReviewVerdict":
        """Extract verdict from agent output text."""
        upper = text.upper()
        if "APPROVED_WITH_COMMENTS" in upper:
            return cls.APPROVED_WITH_COMMENTS
        if "NEEDS_REVISION" in upper:
            return cls.NEEDS_REVISION
        if "REJECTED" in upper:
            return cls.REJECTED
        if "APPROVED" in upper:
            return cls.APPROVED
        return cls.NEEDS_REVISION

    def can_proceed(self) -> bool:
        """Return True if the pipeline can proceed past this verdict."""
        return self in (self.APPROVED, self.APPROVED_WITH_COMMENTS)


class AutomationVerdict(str, Enum):
    """Verdict returned by AutomationReviewAgent (code review)."""
    APPROVED       = "APPROVED"
    NEEDS_REVISION = "NEEDS_REVISION"

    @classmethod
    def from_text(cls, text: str) -> "AutomationVerdict":
        """Extract verdict from agent output text."""
        if "NEEDS_REVISION" in text.upper():
            return cls.NEEDS_REVISION
        if "APPROVED" in text.upper():
            return cls.APPROVED
        return cls.NEEDS_REVISION

    def can_proceed(self) -> bool:
        return self == self.APPROVED


class ReleaseRecommendation(str, Enum):
    """Release recommendation from SprintSummaryAgent."""
    GO              = "GO"
    CONDITIONAL_GO  = "CONDITIONAL_GO"
    NO_GO           = "NO_GO"

    @classmethod
    def from_text(cls, text: str) -> "ReleaseRecommendation":
        """Extract recommendation from agent output text."""
        upper = text.upper()
        if "CONDITIONAL_GO" in upper:
            return cls.CONDITIONAL_GO
        if "NO_GO" in upper:
            return cls.NO_GO
        if "GO" in upper:
            return cls.GO
        return cls.NO_GO


class AutomationDecision(str, Enum):
    """Automation decision for a single scenario."""
    AUTOMATE = "AUTOMATE"
    MANUAL   = "MANUAL"
    PARTIAL  = "PARTIAL"
    DEFER    = "DEFER"


class RiskLevel(str, Enum):
    """Risk level from DefectPredictionAgent."""
    CRITICAL   = "CRITICAL"
    HIGH       = "HIGH"
    MEDIUM     = "MEDIUM"
    LOW        = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"


# ─────────────────────────────────────────────────────────────────────────────
# Structured data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineContext:
    """
    Holds all outputs from every pipeline stage.
    Passed between stages so each agent has access to all prior outputs.
    """
    # Input
    requirement: str = ""
    jira_story_id: str = ""

    # Stage outputs (populated as pipeline progresses)
    analysis: str = ""
    ambiguity_report: str = ""
    impact_report: str = ""
    key_scenarios: str = ""
    test_cases: str = ""
    review: str = ""
    recommendation: str = ""
    reuse_report: str = ""
    scripts: str = ""
    automation_review: str = ""
    test_data: str = ""
    defects: str = ""
    rtm: str = ""
    execution_results: str = ""
    defect_classification: str = ""
    sprint_summary: str = ""
    retrospective: str = ""

    # Derived status fields (set by DecisionEngine)
    ambiguity_status: AmbiguityStatus = AmbiguityStatus.NEEDS_CLARIFICATION
    review_verdict: ReviewVerdict = ReviewVerdict.NEEDS_REVISION
    automation_verdict: AutomationVerdict = AutomationVerdict.NEEDS_REVISION
    release_recommendation: ReleaseRecommendation = ReleaseRecommendation.NO_GO

    # Pipeline metadata
    req_hash: str = ""
    pipeline_stage: str = "NOT_STARTED"
    stages_completed: List[str] = field(default_factory=list)
    stages_skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def mark_complete(self, stage: str) -> None:
        """Mark a pipeline stage as completed."""
        if stage not in self.stages_completed:
            self.stages_completed.append(stage)
        self.pipeline_stage = stage

    def mark_skipped(self, stage: str, reason: str = "") -> None:
        """Mark a pipeline stage as skipped."""
        entry = f"{stage}: {reason}" if reason else stage
        if entry not in self.stages_skipped:
            self.stages_skipped.append(entry)

    def add_error(self, stage: str, error: str) -> None:
        """Record an error from a pipeline stage."""
        self.errors.append(f"[{stage}] {error}")

    def is_complete(self) -> bool:
        """Return True if the pipeline has reached the final stage."""
        return "retrospective" in self.stages_completed

    def summary(self) -> dict:
        """Return a summary dict for logging/reporting."""
        return {
            "req_hash": self.req_hash,
            "jira_story_id": self.jira_story_id,
            "pipeline_stage": self.pipeline_stage,
            "stages_completed": len(self.stages_completed),
            "stages_skipped": len(self.stages_skipped),
            "errors": len(self.errors),
            "ambiguity_status": self.ambiguity_status.value,
            "review_verdict": self.review_verdict.value,
            "automation_verdict": self.automation_verdict.value,
            "release_recommendation": self.release_recommendation.value,
        }


@dataclass
class ClarificationRequest:
    """
    Structured clarification request produced by AmbiguityAnalyzer
    when status == NEEDS_CLARIFICATION.
    """
    status: AmbiguityStatus = AmbiguityStatus.NEEDS_CLARIFICATION
    questions: List[str] = field(default_factory=list)
    blocker_count: int = 0
    critical_count: int = 0
    raw_report: str = ""

    @classmethod
    def from_text(cls, text: str) -> "ClarificationRequest":
        """Parse a ClarificationRequest from AmbiguityAnalyzer output."""
        status = AmbiguityStatus.from_text(text)

        # Extract questions (lines starting with Q1., Q2., etc.)
        questions = re.findall(r'Q\d+\.\s+(.+?)(?:\s+—\s+Affects:|$)', text, re.MULTILINE)

        # Count blockers and criticals
        blocker_count = len(re.findall(r'Severity:\s*BLOCKER', text, re.IGNORECASE))
        critical_count = len(re.findall(r'Severity:\s*CRITICAL', text, re.IGNORECASE))

        return cls(
            status=status,
            questions=questions,
            blocker_count=blocker_count,
            critical_count=critical_count,
            raw_report=text,
        )

    def needs_human_input(self) -> bool:
        """Return True if human clarification is required before proceeding."""
        return self.status == AmbiguityStatus.NEEDS_CLARIFICATION


@dataclass
class TestCaseMetrics:
    """Metrics extracted from TestGenerator output."""
    total_count: int = 0
    functional_count: int = 0
    negative_count: int = 0
    boundary_count: int = 0
    security_count: int = 0
    integration_count: int = 0
    automation_eligible: int = 0
    requirements_covered: int = 0
    tc_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str) -> "TestCaseMetrics":
        """Extract metrics from TestGenerator output."""
        tc_ids = list(set(re.findall(r'\bTC-[A-Z]+-\d{3}\b', text)))

        def _extract_int(pattern: str) -> int:
            m = re.search(pattern, text, re.IGNORECASE)
            return int(m.group(1)) if m else 0

        return cls(
            total_count=len(tc_ids),
            functional_count=_extract_int(r'Functional\s*:\s*(\d+)'),
            negative_count=_extract_int(r'Negative\s*:\s*(\d+)'),
            boundary_count=_extract_int(r'Boundary\s*:\s*(\d+)'),
            security_count=_extract_int(r'Security\s*:\s*(\d+)'),
            integration_count=_extract_int(r'Integration\s*:\s*(\d+)'),
            automation_eligible=_extract_int(r'Automation Eligible\s*:\s*(\d+)'),
            requirements_covered=_extract_int(r'Requirements Covered\s*:\s*(\d+)'),
            tc_ids=tc_ids,
        )


@dataclass
class RTMMetrics:
    """Metrics extracted from RTMAgent output."""
    compliance_score: int = 0
    total_requirements: int = 0
    total_test_cases: int = 0
    automated_count: int = 0
    automation_percentage: float = 0.0
    pipeline_verdict: str = ""

    @classmethod
    def from_text(cls, text: str) -> "RTMMetrics":
        """Extract RTM metrics from RTMAgent output."""
        def _extract_int(pattern: str) -> int:
            m = re.search(pattern, text, re.IGNORECASE)
            return int(m.group(1)) if m else 0

        def _extract_float(pattern: str) -> float:
            m = re.search(pattern, text, re.IGNORECASE)
            return float(m.group(1)) if m else 0.0

        # Extract compliance score
        score_match = re.search(r'COMPLIANCE READINESS SCORE[:\s]+(\d+)', text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0

        # Extract pipeline verdict
        verdict_match = re.search(
            r'Pipeline Verdict\s*:\s*(APPROVED[_A-Z]*|NEEDS_REVISION|REJECTED)',
            text, re.IGNORECASE
        )
        verdict = verdict_match.group(1) if verdict_match else ""

        return cls(
            compliance_score=score,
            total_requirements=_extract_int(r'Total Requirements\s*:\s*(\d+)'),
            total_test_cases=_extract_int(r'Total Test Cases\s*:\s*(\d+)'),
            automated_count=_extract_int(r'Automation: Yes\s*:\s*(\d+)'),
            automation_percentage=_extract_float(r'Automation: Yes\s*:\s*\d+\s*\((\d+\.?\d*)%\)'),
            pipeline_verdict=verdict,
        )

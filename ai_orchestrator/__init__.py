"""
ai_orchestrator — Production AI QA Orchestrator Package
========================================================
This package is the canonical import path for all AI orchestrator modules.

The implementation lives in ai_orchestrator_v1/ (preserved as reference).
This package re-exports everything from there so that:
  - Existing smoke tests (tests/test_ci_smoke.py) continue to pass
  - New code imports from ai_orchestrator directly
  - ai_orchestrator_v1/ is never modified

Architecture Principle:
  AI DECIDES / RECOMMENDS
  CODE VALIDATES
  FRAMEWORK EXECUTES
  HUMAN APPROVES CRITICAL DECISIONS
  RTM PROVIDES TRACEABILITY
"""

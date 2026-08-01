"""
ai_orchestrator.schemas — Pydantic models for structured agent output validation.

Every agent output that flows between pipeline stages is validated against
a schema before being passed to the next agent. Invalid output is rejected
and the agent is retried rather than silently passing bad data downstream.

Architectural Principle:
  CODE VALIDATES — deterministic schema validation catches LLM hallucinations.
  Never rely on free-form LLM output for structured data.
"""

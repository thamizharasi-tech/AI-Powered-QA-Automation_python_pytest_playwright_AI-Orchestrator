"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          AI QA ORCHESTRATOR — REQUIREMENT ENTRY POINT                       ║
║          Full Agile Pipeline: Jira Story → Sprint QA Summary                ║
╚══════════════════════════════════════════════════════════════════════════════╝

HOW TO USE
==========

1. Paste your Jira story / requirement text into the REQUIREMENT variable below.

2. Set your Jira Story ID (optional but recommended for traceability).

3. Configure pipeline options:
     FORCE_RERUN       — True  = re-run all agents (ignore cache)
                         False = use cached outputs if available (faster)
     RUN_TESTS         — True  = execute pytest after code generation
                         False = generate artifacts only (no test execution)
     PAUSE_ON_AMBIGUITY — True  = pause if requirements are unclear (recommended)
                          False = proceed despite ambiguities (CI/CD mode)

4. Run:
     python run_pipeline.py

OUTPUT ARTIFACTS
================
  ✅ Requirement Analysis    → pipeline_state/pipeline_state.xlsx
  ✅ Ambiguity Report        → printed to console
  ✅ Impact Analysis         → printed to console
  ✅ Test Cases              → pipeline_state/pipeline_state.xlsx (Test Cases sheet)
  ✅ Test Review             → printed to console
  ✅ Automation Scripts      → tests/ui/test_<feature>.py or tests/api/test_<feature>.py
  ✅ Test Data               → testData/API_testData.xlsx
  ✅ Defect Predictions      → printed to console (FMEA risk register)
  ✅ RTM                     → pipeline_state/rtm_store.xlsx
  ✅ Sprint QA Summary       → printed to console
  ✅ Retrospective Insights  → printed to console

LLM PROVIDER
============
  Currently configured: Amazon Bedrock (Claude)
  Profile: nimbus-bedrock | Region: us-west-2
  Config:  config/config.json  (copy from config/config.example.json)

  To change provider: edit "provider" in config/config.json
  To add a new provider: see ai_orchestrator/providers/__init__.py
"""

import os
import sys
from pathlib import Path

# ── Ensure project root is on sys.path ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────────────────────────────────────
#  ✏️  EDIT HERE — Paste your requirement below
# ─────────────────────────────────────────────────────────────────────────────

REQUIREMENT = """
Story ID: OHRM-LEAVE-001
Title: Apply for Leave
User Story:
As an employee, I want to apply for leave by selecting a leave type, date range, and reason, so that my leave request can be submitted for approval.
Acceptance Criteria
Employee can navigate to Leave → Apply.
Employee can select an available leave type.
Employee can select a valid From Date and To Date.
System calculates/displays the requested leave duration.
Employee can enter an optional comment/reason.
Employee can submit the leave request.
Successfully submitted request appears in My Leave.
A leave request with an invalid date range must not be submitted.
Employee cannot submit a request when insufficient leave balance exists.
Appropriate validation should be displayed when mandatory information is missing.
Employee should not be able to create a duplicate leave request for the same period if overlapping requests are not allowed.
Submitted leave should have an appropriate status such as Pending.
"""

# Optional: Jira Story ID for traceability (e.g. "HRM-202", "PROJ-101")
JIRA_STORY_ID = "HRM-202"

# ─────────────────────────────────────────────────────────────────────────────
#  ⚙️  PIPELINE OPTIONS
# ─────────────────────────────────────────────────────────────────────────────

# Set True to bypass cache and re-run all agents from scratch
# Set False (default) to reuse cached outputs for unchanged requirements
# Set True to bypass cache and re-run all agents from scratch
# Set False (default) to reuse cached outputs for unchanged requirements
FORCE_RERUN = os.environ.get("FORCE_RERUN", "0").strip() == "1"

# Set True to execute pytest after automation code is generated
# Set False (default) to generate artifacts only
RUN_TESTS = os.environ.get("RUN_TESTS", "0").strip() == "1"

# Set True to pause pipeline if requirements are ambiguous (recommended for production)
# Set False (default) to proceed through all agents regardless of ambiguity status
PAUSE_ON_AMBIGUITY = os.environ.get("PAUSE_ON_AMBIGUITY", "0").strip() != "0"

# ─────────────────────────────────────────────────────────────────────────────
#  🚀  PIPELINE EXECUTION — Do not edit below this line
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    """Run the full Agile QA pipeline and return exit code (0=success, 1=error)."""

    # Validate requirement is not empty
    req = REQUIREMENT.strip()
    if not req or req == "# Paste your requirement here":
        print("❌ ERROR: REQUIREMENT is empty.")
        print("   Edit the REQUIREMENT variable in run_pipeline.py and try again.")
        return 1

    # Validate config.json exists
    config_path = PROJECT_ROOT / "config" / "config.json"
    if not config_path.exists():
        print("❌ ERROR: config/config.json not found.")
        print("   Run: copy config\\config.example.json config\\config.json")
        print("   Then ensure your AWS profile 'nimbus-bedrock' is configured.")
        return 1

    print("\n" + "═" * 70)
    print("  AI QA ORCHESTRATOR — STARTING PIPELINE")
    print("═" * 70)
    print(f"  Jira Story ID      : {JIRA_STORY_ID or '(not set)'}")
    print(f"  Force Re-run       : {FORCE_RERUN}")
    print(f"  Run Tests          : {RUN_TESTS}")
    print(f"  Pause on Ambiguity : {PAUSE_ON_AMBIGUITY}")
    print(f"  Requirement preview: {req[:80]}...")
    print("═" * 70)

    try:
        from ai_orchestrator.orchestrator.workflow import AgileQAWorkflow

        workflow = AgileQAWorkflow(
            max_retries=3,
            timeout_seconds=120,
        )

        context = workflow.run(
            requirement=req,
            jira_story_id=JIRA_STORY_ID,
            force_rerun=FORCE_RERUN,
            run_tests=RUN_TESTS,
            pause_on_ambiguity=PAUSE_ON_AMBIGUITY,
        )

        # Print key outputs
        _print_section("AMBIGUITY REPORT", context.ambiguity_report)
        _print_section("SPRINT QA SUMMARY", context.sprint_summary)
        _print_section("RETROSPECTIVE INSIGHTS", context.retrospective)

        # Print pipeline summary
        summary = context.summary()
        print("\n" + "═" * 70)
        print("  PIPELINE COMPLETE")
        print("═" * 70)
        print(f"  Stages completed   : {summary['stages_completed']}")
        print(f"  Ambiguity status   : {summary['ambiguity_status']}")
        print(f"  Review verdict     : {summary['review_verdict']}")
        print(f"  Automation verdict : {summary['automation_verdict']}")
        print(f"  Release decision   : {summary['release_recommendation']}")
        print(f"  Errors             : {summary['errors']}")
        print("\n  Output files:")
        print(f"    📊 Pipeline state : ai_orchestrator/pipeline_state/pipeline_state.xlsx")
        print(f"    📋 RTM store      : ai_orchestrator/pipeline_state/rtm_store.xlsx")
        print(f"    📁 Test data      : testData/API_testData.xlsx")
        print(f"    🧪 Test scripts   : tests/ui/ or tests/api/")
        print("═" * 70)

        return 0 if summary["errors"] == 0 else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user.")
        return 1
    except Exception as exc:
        print(f"\n❌ Pipeline failed with error: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        return 1


def _print_section(title: str, content: str, max_chars: int = 2000) -> None:
    """Print a pipeline output section with truncation."""
    if not content:
        return
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print("─" * 70)
    if len(content) > max_chars:
        print(content[:max_chars])
        print(f"\n  ... [truncated — full output in pipeline_state.xlsx Cache sheet]")
    else:
        print(content)


if __name__ == "__main__":
    sys.exit(main())

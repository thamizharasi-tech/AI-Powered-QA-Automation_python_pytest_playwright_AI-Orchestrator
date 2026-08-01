"""
conftest_allure_patch.py — Allure FileLogger path patcher
==========================================================
Patches AllureFileLogger.__init__ to handle two common issues:

1. Windows MAX_PATH (260 char) limit — if the project path is very long,
   UUID-named allure result files (41 chars) may exceed MAX_PATH.
   In that case, results are written to %TEMP%/qa_allure/allure-results
   and copied back to the project directory after the test run.

2. Non-writable project path — if the project directory is virtualised
   or owned by a different user, writes are redirected to TEMP.

This module is imported at the top of conftest.py so the patch is applied
BEFORE the allure plugin's pytest_configure creates an AllureFileLogger.
Works on any machine regardless of project path length.
"""
import tempfile
import uuid
from pathlib import Path


def _get_writable_allure_dir(requested_dir: Path) -> Path:
    """
    Return a writable directory for allure results.

    Strategy:
      1. Try the requested directory with a UUID-length probe file.
         If it works → use it as-is (normal case, short paths).
      2. If it fails (MAX_PATH exceeded or not writable) → fall back to
         %TEMP%/qa_allure/allure-results which is always short and writable.

    Parameters
    ----------
    requested_dir : Path — the directory allure wants to write to

    Returns
    -------
    Path — a guaranteed-writable directory
    """
    try:
        requested_dir.mkdir(parents=True, exist_ok=True)
        # Probe with a UUID-length filename (same pattern allure uses)
        probe = requested_dir / f"{uuid.uuid4()}-result.json"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return requested_dir  # ✅ Writable and within MAX_PATH
    except (OSError, PermissionError):
        # Fall back to a short temp path that works on any machine
        fallback = Path(tempfile.gettempdir()) / "qa_allure" / "allure-results"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def patch_allure_file_logger():
    """
    Monkey-patch AllureFileLogger.__init__ to use a writable directory.

    The patch is transparent — if the requested directory is writable and
    within MAX_PATH, it is used unchanged. Only when there is a problem
    does it redirect to the temp fallback.
    """
    try:
        from allure_commons.logger import AllureFileLogger
        _original_init = AllureFileLogger.__init__

        def _patched_init(self, report_dir, clean=False):
            requested = Path(report_dir).absolute()
            writable  = _get_writable_allure_dir(requested)

            if writable != requested:
                print(
                    f"[allure_patch] MAX_PATH or write issue detected.\n"
                    f"  Requested : {requested}\n"
                    f"  Redirected: {writable}\n"
                    f"  Reports will be copied to the project directory after the run."
                )

            _original_init(self, str(writable), clean)

        AllureFileLogger.__init__ = _patched_init

    except Exception as exc:
        print(f"[allure_patch] WARNING: Could not patch AllureFileLogger: {exc}")


# Apply patch immediately when this module is imported
patch_allure_file_logger()

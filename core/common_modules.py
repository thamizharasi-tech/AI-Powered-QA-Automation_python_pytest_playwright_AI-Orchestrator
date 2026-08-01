"""
common_modules — Shared Framework Utilities
============================================
Provides:
  - result()     : structured pass/fail logging for test steps
  - log_backup() : copy HTML report to the backup directory

NOTE: pytest_configure is intentionally NOT defined here.
      All report path configuration is handled exclusively in conftest.py
      to avoid duplicate hook conflicts.
"""

import datetime
import os
import shutil
import warnings

from core.e2e_testData import backup_dir


# ─────────────────────────────────────────────────────────────────────────────
# result() — Structured test step logging
# ─────────────────────────────────────────────────────────────────────────────

def result(status: str, expected: str, actual: str) -> None:
    """
    Log a structured pass/fail result for a test step and assert accordingly.

    Prints "Expected behaviour" and "Actual behaviour" lines that are captured
    by conftest.py's stdout hook and surfaced in the AI Dashboard as
    Validation Results.

    Parameters
    ----------
    status   : str — one of:
                 "passed"             → prints + assert True
                 "failed"             → prints + assert False (fails the test)
                 "verificationPassed" → prints only (soft pass, no assert)
                 "verificationFailed" → prints + emits UserWarning (soft fail,
                                        does NOT fail the test — use for
                                        non-blocking checks only)
    expected : str — description of the expected behaviour
    actual   : str — description of the actual observed behaviour

    Examples
    --------
    result("passed",  "Dashboard should be visible", "Dashboard is visible")
    result("failed",  "Dashboard should be visible", "Dashboard NOT visible")
    result("verificationPassed", "Toast should appear", "Toast appeared")
    result("verificationFailed", "Icon should be green", "Icon is grey")
    """
    print(f"Expected behaviour : => {expected}")
    print(f"Actual behaviour   : => {actual}")
    print()

    if status == "passed":
        assert True

    elif status == "failed":
        assert False, f"FAILED — Expected: {expected} | Actual: {actual}"

    elif status == "verificationPassed":
        # Soft pass — logged but does not affect test outcome
        pass

    elif status == "verificationFailed":
        # Soft fail — emits a warning but does NOT fail the test.
        # Use only for non-blocking checks (e.g. cosmetic issues).
        # If the check is business-critical, use status="failed" instead.
        warnings.warn(
            f"Verification failed — Expected: {expected} | Actual: {actual}",
            UserWarning,
            stacklevel=2,
        )

    else:
        # Unknown status — treat as a hard failure to surface miscalls
        assert False, (
            f"result() called with unknown status='{status}'. "
            f"Valid values: passed | failed | verificationPassed | verificationFailed"
        )


# ─────────────────────────────────────────────────────────────────────────────
# log_backup() — Copy HTML report to the timestamped backup directory
# ─────────────────────────────────────────────────────────────────────────────

def log_backup(file: str, cloud_env: str) -> None:
    """
    Copy an HTML report file to the backup directory with a timestamp suffix.

    Parameters
    ----------
    file      : str — absolute path to the HTML report file
    cloud_env : str — environment name used in the backup filename
                      (e.g. "QA", "UAT", "PROD")
    """
    if not file.endswith(".html"):
        return

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(
        backup_dir,
        f"Test_Report_{cloud_env}_{timestamp}.html",
    )
    shutil.copy(file, dest)
    print(f"Report backed up → {dest}")

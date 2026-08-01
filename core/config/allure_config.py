"""
core/config/allure_config.py — Allure Configuration & Label Helpers
=====================================================================
Centralises all Allure-related configuration:
  - Path constants (results dir, report dir, archive dir, categories file)
  - Allure CLI executable discovery
  - Allure label derivation from pytest item (feature / story / title)
  - categories.json copy helper

All path constants are derived from the project root so they work
regardless of which directory pytest is launched from.

Usage (in conftest.py):
    from core.config.allure_config import (
        ALLURE_RESULTS, ALLURE_REPORT, ALLURE_ARCHIVE,
        ALLURE_CATEGORIES, MAX_ARCHIVE_COUNT,
        find_allure_executable, derive_allure_labels,
        copy_allure_categories,
    )
"""

import os
import re
import shutil
from pathlib import Path

from core.logger.logger import get_logger

log = get_logger(__name__)

# ── Project paths ─────────────────────────────────────────────────────────────
# On Windows the project may live under a different user profile than the one
# running Python (e.g. project owned by slua_* but Python runs as ragurama).
# In that case Path(__file__).resolve() and os.getcwd() both point to the
# virtualised/redirected path which is NOT writable by the running user.
#
# Strategy: try to write a probe file to the CWD-based report dir.
# If that fails, fall back to the running user's TEMP directory so that
# allure results are always written to a writable location.
import os as _os
import tempfile as _tempfile

def _writable_report_root() -> Path:
    """
    Return a writable report root that supports long filenames (UUID-based).

    On machines where the project path is short enough (< ~220 chars),
    the standard project testReport directory is used directly.

    On machines where the path is too long (Windows MAX_PATH = 260 chars)
    or the directory is not writable, falls back to %TEMP%/qa_allure so
    that allure results can always be written. The report_manager then
    copies the generated reports back to the project directory.

    This function works on any machine regardless of where the project
    is cloned — no hardcoded paths.
    """
    import uuid as _uuid
    # Use CWD so this works regardless of which user cloned the project
    cwd_root = Path(_os.getcwd())
    candidate = cwd_root / "testReport" / "Execution_Backup" / "report"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # Probe with a UUID-length filename (same pattern allure uses)
        probe = candidate / f"{_uuid.uuid4()}-result.json"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate  # ✅ Short path, writable — use project directory
    except (OSError, PermissionError):
        # Path too long or not writable — use system temp (always short + writable)
        fallback = Path(_tempfile.gettempdir()) / "qa_allure"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

PROJECT_ROOT    = Path(__file__).resolve().parent.parent.parent
REPORT_ROOT     = _writable_report_root()
ALLURE_RESULTS  = REPORT_ROOT / "allure-results"
ALLURE_REPORT   = REPORT_ROOT / "allure-report"
# Archive stays in project if possible, otherwise alongside temp reports
_project_archive = Path(_os.getcwd()) / "testReport" / "Execution_Backup" / "archive"
ALLURE_ARCHIVE  = _project_archive if REPORT_ROOT.is_relative_to(Path(_os.getcwd())) else REPORT_ROOT.parent / "archive"
ALLURE_CATEGORIES = PROJECT_ROOT / "allure" / "categories.json"

# Maximum number of archived reports to keep (older ones are pruned automatically)
MAX_ARCHIVE_COUNT: int = int(os.environ.get("ALLURE_ARCHIVE_KEEP", "10"))


# ─────────────────────────────────────────────────────────────────────────────
# Allure CLI discovery
# ─────────────────────────────────────────────────────────────────────────────

def find_allure_executable() -> str:
    """
    Locate the Allure CLI executable.

    Search order:
      1. System PATH  (works on Linux/Mac/CI after `allure` is installed)
      2. ALLURE_HOME env var  (e.g. ALLURE_HOME=C:\\allure-2.44.0)
      3. Common Windows fallback path

    Returns
    -------
    str — absolute path to the allure executable

    Raises
    ------
    FileNotFoundError — if Allure CLI cannot be found
    """
    # 1. System PATH
    allure_exe = shutil.which("allure")
    if allure_exe:
        log.debug("Allure CLI found on PATH: %s", allure_exe)
        return allure_exe

    # 2. ALLURE_HOME environment variable
    allure_home = os.environ.get("ALLURE_HOME")
    if allure_home:
        suffix = "bin\\allure.bat" if os.name == "nt" else "bin/allure"
        candidate = Path(allure_home) / suffix
        if candidate.exists():
            log.debug("Allure CLI found via ALLURE_HOME: %s", candidate)
            return str(candidate)

    # 3. Common Windows installation path
    win_fallback = Path(r"C:\allure-2.44.0\allure-2.44.0\bin\allure.bat")
    if win_fallback.exists():
        log.debug("Allure CLI found at Windows fallback: %s", win_fallback)
        return str(win_fallback)

    raise FileNotFoundError(
        "Allure CLI not found.\n"
        "Options:\n"
        "  1. Add allure to your system PATH\n"
        "  2. Set ALLURE_HOME env var to your Allure installation directory\n"
        "  3. Install via: scoop install allure  (Windows)\n"
        "                  brew install allure   (macOS)\n"
        "                  apt install allure    (Linux)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Allure label derivation
# ─────────────────────────────────────────────────────────────────────────────

def _humanize(value: str) -> str:
    """
    Convert a snake_case or kebab-case identifier to Title Case.

    Examples:
        "test_valid_login"  → "Test Valid Login"
        "test-add-employee" → "Test Add Employee"
        "test_login[v1]"    → "Test Login"
    """
    normalized = re.sub(r"[_\-]+", " ", value)
    normalized = re.sub(r"\[.*\]$", "", normalized)   # strip parametrize suffix
    return normalized.strip().title()


def derive_allure_labels(item) -> tuple:
    """
    Derive Allure feature / story / title labels from a pytest item.

    Logic:
      - feature = parent directory name (e.g. "Ui", "Api")
                  + class name if present (e.g. "Ui / Test Login")
      - story   = humanized test function name
      - title   = same as story

    These labels are applied as dynamic Allure labels in pytest_runtest_setup
    for tests that don't already have @allure.feature / @allure.story decorators.

    Parameters
    ----------
    item : pytest.Item — the test item being set up

    Returns
    -------
    tuple[str, str, str] — (feature, story, title)
    """
    node_path = Path(str(item.fspath))
    directory = node_path.parent.name.title()

    # If the immediate parent is not "ui" or "api", use the grandparent name
    if directory.lower() not in {"ui", "api"} and node_path.parent.parent.name:
        directory = node_path.parent.parent.name.title()

    feature = directory
    if getattr(item, "cls", None):
        class_name = _humanize(item.cls.__name__)
        feature = f"{feature} / {class_name}"

    story = _humanize(item.name)
    title = story
    return feature, story, title


# ─────────────────────────────────────────────────────────────────────────────
# categories.json helper
# ─────────────────────────────────────────────────────────────────────────────

def copy_allure_categories(source: Path, destination_dir: Path) -> None:
    """
    Copy allure/categories.json into the allure-results directory.

    categories.json defines how Allure categorizes test failures
    (e.g. "Product defects", "Test defects", "Broken tests").
    It must be present in the results directory before `allure generate` runs.

    Parameters
    ----------
    source          : Path — path to allure/categories.json
    destination_dir : Path — allure-results directory to copy into
    """
    if not source.exists():
        log.debug("categories.json not found at %s — skipping copy", source)
        return
    try:
        shutil.copy(source, destination_dir / "categories.json")
        log.debug("Copied categories.json → %s", destination_dir)
    except OSError as exc:
        log.warning("Could not copy Allure categories file: %s", exc)

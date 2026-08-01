"""
conftest.py — pytest Fixtures & Hooks
=======================================
This file contains ONLY:
  - pytest fixtures  (page, cloud_env)
  - pytest hooks     (pytest_configure, pytest_sessionstart, pytest_sessionfinish,
                      pytest_runtest_setup, pytest_runtest_makereport,
                      pytest_runtest_logreport)

All helper logic has been moved to dedicated core modules:
  - core/config/allure_config.py   — Allure paths, label derivation, CLI finder
  - core/reports/report_manager.py — Archive, Allure generate, AI Dashboard
  - core/logger/logger.py          — Structured logging

This separation keeps conftest.py focused and easy to read.
"""

# ── Windows Unicode fix ───────────────────────────────────────────────────────
# Ensures emoji and Unicode characters (✅ ❌ ⚠️) render correctly on Windows
# terminals that default to cp1252 encoding. Safe no-op on Linux/Mac.
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Allure FileLogger path patch ──────────────────────────────────────────────
# Must be imported BEFORE allure_pytest loads so that AllureFileLogger.__init__
# is patched before the allure plugin's pytest_configure creates an instance.
# This redirects allure results to a writable path on Windows environments
# where the project path is virtualised/not writable by the running user.
import conftest_allure_patch  # noqa: F401

import json
import shutil
from pathlib import Path

import allure
import pytest
from playwright.sync_api import sync_playwright

# ── Core framework imports ────────────────────────────────────────────────────
from core.config.allure_config import (
    ALLURE_RESULTS,
    ALLURE_CATEGORIES,
    derive_allure_labels,
    copy_allure_categories,
)
from core.reports.report_manager import ReportManager
from core.logger.logger import get_logger
from core.e2e_testData import (
    testReport_UIScreenshotsPath,
    testReport_UIVideosPath,
    testReport_UITracesPath,
    browser_name,
    headlessMode,
    storage_state_path,
)
from core.ui.session_manager import SessionManager

log = get_logger(__name__)

# ── Report root (used by pytest_configure to set alluredir) ──────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent
_REPORT_ROOT  = _PROJECT_ROOT / "testReport" / "Execution_Backup" / "report"


# =============================================================================
# HOOKS
# =============================================================================

@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """
    Create report directories and patch the allure FileLogger to use a
    writable path.

    Uses trylast=True so this hook runs AFTER the allure plugin's
    pytest_configure has already created AllureFileLogger. We then
    monkey-patch its _report_dir to point to ALLURE_RESULTS (which is
    guaranteed writable via the probe in allure_config.py).
    """
    _REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)

    # Override allure_report_dir option so future allure plugin calls use
    # the correct writable path.
    try:
        config.option.allure_report_dir = str(ALLURE_RESULTS)
    except AttributeError:
        pass

    # Override HTML report path to absolute so it always writes to the
    # project testReport directory regardless of which directory pytest
    # is launched from (prevents reports being created inside tests/ folder).
    html_report_path = _REPORT_ROOT / "pytest_html_report.html"
    html_report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config.option.htmlpath = str(html_report_path)
    except AttributeError:
        pass

    # Monkey-patch AllureFileLogger._report_dir on all registered instances
    # so that result JSON files are written to the writable ALLURE_RESULTS dir.
    try:
        import allure_commons
        for plugin in allure_commons.plugin_manager.get_plugins():
            if hasattr(plugin, "_report_dir"):
                plugin._report_dir = ALLURE_RESULTS
                ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
                log.info("Patched allure FileLogger._report_dir → %s", ALLURE_RESULTS)
    except Exception as exc:
        log.warning("Could not patch allure FileLogger: %s", exc)

    log.info("Allure results directory: %s", ALLURE_RESULTS)


def pytest_sessionstart(session):
    """
    1. Patch AllureFileLogger._report_dir to the writable ALLURE_RESULTS path.
       By sessionstart, all pytest_configure hooks have run and AllureFileLogger
       is registered in allure_commons.plugin_manager. We patch it here so that
       all subsequent allure writes go to the correct writable directory.

    2. Clean the allure-results directory so stale results from previous runs
       don't pollute the new report.

    3. Copy categories.json into the results directory.

    Windows note: files/directories may be locked by a previous process.
    Locked entries are skipped with a warning rather than crashing with
    INTERNALERROR (PermissionError / WinError 32).
    """
    # ── Patch AllureFileLogger._report_dir ────────────────────────────────────
    try:
        import allure_commons
        pm = allure_commons._core.MetaPluginManager.get_plugin_manager()
        patched = 0
        for plugin in pm.get_plugins():
            if hasattr(plugin, "_report_dir"):
                plugin._report_dir = ALLURE_RESULTS
                patched += 1
        if patched:
            log.info("Patched %d allure FileLogger(s) → %s", patched, ALLURE_RESULTS)
        else:
            log.debug("No allure FileLogger found to patch (allure may not be active).")
    except Exception as exc:
        log.warning("Could not patch allure FileLogger._report_dir: %s", exc)

    # ── Clean allure-results directory ────────────────────────────────────────
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    for entry in ALLURE_RESULTS.iterdir():
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        except (PermissionError, OSError) as exc:
            log.warning(
                "Could not remove '%s' from allure-results (file locked by another process): %s",
                entry.name, exc,
            )
    # Ensure the directory still exists after cleanup (allure plugin needs it)
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    copy_allure_categories(ALLURE_CATEGORIES, ALLURE_RESULTS)


def pytest_runtest_setup(item):
    """
    Apply dynamic Allure labels (feature / story / title) before each test.

    Only applies labels for tests that don't already have @allure.feature /
    @allure.story decorators. Labels are derived from the file path and
    class/function name by core.config.allure_config.derive_allure_labels().
    """
    feature, story, title = derive_allure_labels(item)
    try:
        allure.dynamic.feature(feature)
        allure.dynamic.story(story)
        allure.dynamic.title(title)
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    """
    Generate all post-test reports after the session ends.

    Delegates to ReportManager.generate_all() which handles:
      1. pytest-html report backup
      2. environment.properties write
      3. Previous Allure report archiving
      4. Allure HTML report generation
      5. AI Dashboard HTML generation
    """
    ReportManager.generate_all(session, exitstatus)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Store the call-phase report on the item so the `page` fixture can
    detect test failure and attach screenshots/traces/videos to Allure.
    Also captures stdout for the pytest_runtest_logreport hook.
    """
    outcome = yield
    report  = outcome.get_result()
    if report.when == "call":
        item.rep_call   = report
        item._capstdout = (getattr(report, "capstdout", "") or "").strip()


def pytest_runtest_logreport(report):
    """
    Patch the Allure result JSON to add captured stdout as a text attachment.

    Bypasses allure.attach() to avoid the duplicate-attachment issue caused
    by allure-pytest's own pytest_runtest_logreport hook. The stdout text is
    written as a plain .txt file and the most-recently modified result JSON
    for this test is updated to reference it.
    """
    if report.when != "call":
        return
    stdout_text = (getattr(report, "capstdout", "") or "").strip()
    if not stdout_text:
        return
    try:
        import uuid as _uuid
        if not ALLURE_RESULTS.exists():
            return

        # Write the attachment text file
        att_filename = f"{_uuid.uuid4()}-attachment.txt"
        att_path     = ALLURE_RESULTS / att_filename
        att_path.write_text(stdout_text, encoding="utf-8")

        # Find the most recently modified result JSON (just written by allure-pytest)
        result_files = sorted(
            ALLURE_RESULTS.glob("*-result.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not result_files:
            return

        result_file = result_files[0]
        result_data = json.loads(result_file.read_text(encoding="utf-8"))

        # Only patch if this result doesn't already have a stdout attachment
        existing_names = [a.get("name", "") for a in result_data.get("attachments", [])]
        if "stdout" in existing_names:
            return

        result_data.setdefault("attachments", []).append({
            "name":   "stdout",
            "source": att_filename,
            "type":   "text/plain",
        })
        result_file.write_text(json.dumps(result_data), encoding="utf-8")

    except Exception:
        pass   # Never fail a test due to attachment patching errors


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def page(request):
    """
    Playwright `page` fixture — provides a fully configured browser page.

    Setup:
      - Launches browser (chromium / firefox / edge) from Excel config
        or E2E_BROWSER env var
      - Creates browser context with video recording
      - Loads storageState.json if it exists (pre-authenticated session)
      - Starts Playwright tracing (screenshots + snapshots + sources)

    Teardown (on FAILURE):
      - Captures full-page screenshot → attached to Allure
      - Stops tracing → trace.zip attached to Allure
      - Attaches failure video to Allure

    Teardown (on PASS):
      - Cleans up screenshot, trace, and video files silently
    """
    with sync_playwright() as p:
        import tempfile as _tempfile
        import uuid as _uuid_mod

        # Sanitise test name — remove parametrize brackets that cause path issues
        test_name = (
            request.node.name
            .replace(" ", "_")
            .replace("/", "_")
            .replace("[", "_")
            .replace("]", "_")
            .replace(":", "_")
        )

        # Use a short temp path for screenshots/traces/videos to avoid MAX_PATH
        # on Windows when the project path is very long.
        def _writable_ui_dir(preferred: str, subdir: str) -> Path:
            """Return preferred path if writable, else fall back to temp."""
            p_path = Path(preferred)
            try:
                p_path.mkdir(parents=True, exist_ok=True)
                probe = p_path / f".probe_{_uuid_mod.uuid4().hex[:8]}"
                probe.write_text("ok")
                probe.unlink()
                return p_path
            except (OSError, PermissionError):
                fallback = Path(_tempfile.gettempdir()) / "qa_ui" / subdir
                fallback.mkdir(parents=True, exist_ok=True)
                return fallback

        screenshots_dir = _writable_ui_dir(testReport_UIScreenshotsPath, "screenshots")
        traces_dir      = _writable_ui_dir(testReport_UITracesPath,       "traces")
        videos_dir      = _writable_ui_dir(testReport_UIVideosPath,       "videos")

        screenshot_path = screenshots_dir / f"{test_name}.png"
        trace_path      = traces_dir      / f"{test_name}.zip"

        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        videos_dir.mkdir(parents=True, exist_ok=True)

        # ── Launch browser ────────────────────────────────────────────────────
        if browser_name == "chromium":
            browser = p.chromium.launch(headless=headlessMode)
        elif browser_name == "firefox":
            browser = p.firefox.launch(headless=headlessMode)
        elif browser_name == "edge":
            browser = p.chromium.launch(headless=headlessMode, channel="msedge")
        else:
            raise ValueError(
                f"Unsupported browser: '{browser_name}'. "
                "Valid values: chromium | firefox | edge"
            )

        log.info("Browser launched: %s (headless=%s)", browser_name, headlessMode)

        # ── Create context ────────────────────────────────────────────────────
        context_kwargs = {
            "record_video_dir":  str(videos_dir),
            "record_video_size": {"width": 640, "height": 360},
        }
        if SessionManager.storage_state_exists(storage_state_path):
            context_kwargs["storage_state"] = storage_state_path
            log.debug("Loaded storage state from: %s", storage_state_path)

        context = browser.new_context(**context_kwargs)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        # ── Yield page to the test ────────────────────────────────────────────
        yield page

        # ── Teardown ──────────────────────────────────────────────────────────
        failed     = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
        video_path = None

        page_video = getattr(page, "video", None)
        if page_video is not None:
            try:
                video_path = page_video.path()
            except Exception:
                video_path = None

        if failed:
            page.screenshot(path=str(screenshot_path), full_page=True)

        context.tracing.stop(path=str(trace_path))
        context.close()
        browser.close()

        if failed:
            ReportManager.attach_file_if_exists(
                screenshot_path, "Failure Screenshot", allure.attachment_type.PNG
            )
            ReportManager.attach_file_if_exists(
                trace_path, "Playwright Trace", allure.attachment_type.TEXT
            )
            if video_path:
                ReportManager.attach_file_if_exists(
                    Path(video_path), "Failure Video", allure.attachment_type.MP4
                )
        else:
            ReportManager.cleanup_file(screenshot_path)
            ReportManager.cleanup_file(trace_path)
            if video_path:
                ReportManager.cleanup_file(Path(video_path))

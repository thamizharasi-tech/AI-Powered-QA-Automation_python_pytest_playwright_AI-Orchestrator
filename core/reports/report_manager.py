"""
core/reports/report_manager.py — Report Generation & Archive Manager
======================================================================
Centralises all post-test report operations:
  - Write environment.properties for Allure
  - Archive the previous Allure report (with configurable retention)
  - Generate the Allure HTML report via CLI
  - Generate the AI Dashboard HTML report
  - Back up the pytest-html report

All logic that was previously inline in conftest.py's pytest_sessionfinish()
hook now lives here, keeping conftest.py clean (hooks + fixtures only).

Usage (in conftest.py):
    from core.reports.report_manager import ReportManager
    ReportManager.generate_all(session, exitstatus)
"""

import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from core.config.allure_config import (
    ALLURE_RESULTS,
    ALLURE_REPORT,
    ALLURE_ARCHIVE,
    MAX_ARCHIVE_COUNT,
    find_allure_executable,
)
from core.logger.logger import get_logger

log = get_logger(__name__)


class ReportManager:
    """
    Static methods for all post-test report generation and archiving.

    Call ReportManager.generate_all(session, exitstatus) from
    pytest_sessionfinish() in conftest.py.
    """

    # ── Public entry point ────────────────────────────────────────────────────

    @staticmethod
    def generate_all(session, exitstatus: int) -> None:
        """
        Run the full post-test report pipeline:
          1. Back up pytest-html report
          2. Write environment.properties
          3. Archive previous Allure report
          4. Generate Allure HTML report
          5. Generate AI Dashboard HTML report

        Parameters
        ----------
        session    : pytest.Session — the pytest session object
        exitstatus : int            — pytest exit code
        """
        from core.utils.XLUtils import read_cloud_env
        from core.common_modules import log_backup
        from core.e2e_testData import browser_name, headlessMode

        cloud_env = read_cloud_env()

        # ── 1. Back up pytest-html report ─────────────────────────────────────
        try:
            report_file_path = session.config.option.htmlpath
            if report_file_path and os.path.exists(report_file_path):
                try:
                    log.info("HTML Report: %s", report_file_path)
                except Exception:
                    pass
                log_backup(report_file_path, cloud_env)
        except Exception as exc:
            try:
                log.warning("Could not back up HTML report: %s", exc)
            except Exception:
                pass

        # ── Guard: check allure-results exists and has result files ───────────
        if not ALLURE_RESULTS.exists():
            try:
                log.warning("No Allure results directory found — skipping report generation.")
            except Exception:
                pass
            return

        result_files    = list(ALLURE_RESULTS.glob("*-result.json"))
        container_files = list(ALLURE_RESULTS.glob("*-container.json"))
        try:
            log.info("Result Files    : %d", len(result_files))
            log.info("Container Files : %d", len(container_files))
        except Exception:
            pass

        if not result_files:
            try:
                log.warning("No Allure result files found — skipping report generation.")
            except Exception:
                pass
            return

        # ── 2. Write environment.properties ───────────────────────────────────
        ReportManager._write_environment_properties(cloud_env, browser_name, headlessMode)

        # ── 3. Archive previous Allure report ─────────────────────────────────
        ReportManager._archive_previous_report(ALLURE_REPORT, ALLURE_ARCHIVE, MAX_ARCHIVE_COUNT)

        # Remove old report directory before regenerating.
        # On Windows, the folder may be locked by a browser or file explorer.
        # We use onerror to skip locked files rather than crashing the session.
        if ALLURE_REPORT.exists():
            def _on_rmtree_error(func, path, exc_info):
                """Silently skip files/dirs that are locked by another process."""
                log.debug(
                    "Could not remove '%s' (file locked by another process) — skipping. "
                    "The Allure CLI --clean flag will handle cleanup.",
                    path,
                )
            try:
                shutil.rmtree(ALLURE_REPORT, onerror=_on_rmtree_error)
            except Exception as exc:
                log.debug("rmtree failed for %s: %s — Allure --clean will handle it.", ALLURE_REPORT, exc)

        # ── 4. Generate Allure HTML report ────────────────────────────────────
        ReportManager._generate_allure_report()

        # ── 5. Generate AI Dashboard ──────────────────────────────────────────
        ReportManager._generate_ai_dashboard()

        # ── 6. Copy reports to project directory (MAX_PATH-safe) ──────────────
        ReportManager._copy_reports_to_project()

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _write_environment_properties(
        cloud_env: str,
        browser: str,
        headless: bool,
    ) -> None:
        """Write environment.properties into the allure-results directory."""
        env_file = ALLURE_RESULTS / "environment.properties"
        try:
            with env_file.open("w", encoding="utf-8") as f:
                f.write(f"Environment={cloud_env}\n")
                f.write(f"Platform={platform.system()}\n")
                f.write(f"Python={platform.python_version()}\n")
                f.write(f"Framework=Pytest\n")
                f.write(f"Browser={browser}\n")
                f.write(f"Headless={headless}\n")
            log.debug("environment.properties written → %s", env_file)
        except Exception as exc:
            log.warning("Could not write environment.properties: %s", exc)

    @staticmethod
    def _archive_previous_report(
        report_dir: Path,
        archive_dir: Path,
        keep: int,
    ) -> None:
        """
        Copy the current Allure report to a timestamped archive directory,
        then prune archives older than `keep` most recent.
        """
        if not report_dir.exists():
            return

        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = archive_dir / f"allure-report_{timestamp}"

        try:
            shutil.copytree(report_dir, destination, dirs_exist_ok=True)
            log.info("Archived previous report → %s", destination)
        except Exception as exc:
            log.warning("Could not archive previous report: %s", exc)
            return

        # Prune old archives
        try:
            archive_items = sorted(
                [child for child in archive_dir.iterdir() if child.is_dir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_archive in archive_items[keep:]:
                shutil.rmtree(old_archive)
                log.info("Removed old archive: %s", old_archive)
        except Exception as exc:
            log.warning("Could not prune old archives: %s", exc)

    @staticmethod
    def _generate_allure_report() -> None:
        """Run `allure generate` to produce the HTML report from allure-results."""
        try:
            allure_exe = find_allure_executable()
            proc = subprocess.run(
                [
                    allure_exe,
                    "generate",
                    str(ALLURE_RESULTS),
                    "-o",
                    str(ALLURE_REPORT),
                    "--clean",
                ],
                capture_output=True,
                text=True,
            )
            if proc.stdout:
                log.info(proc.stdout.strip())
            if proc.returncode != 0:
                log.error("Allure report generation failed:\n%s", proc.stderr)
                return

            if (ALLURE_REPORT / "index.html").exists():
                log.info("✅ Allure Report Generated Successfully")
                log.info("📂 Report Location: %s", ALLURE_REPORT / "index.html")
            else:
                log.warning("❌ Report generation completed but index.html not found.")

        except FileNotFoundError as exc:
            log.error(str(exc))
        except Exception as exc:
            log.error("❌ Unexpected error while generating Allure report: %s", exc)

    @staticmethod
    def _generate_ai_dashboard() -> None:
        """Generate the AI Dashboard HTML report from allure-results JSON files."""
        try:
            from ai_orchestrator.agents.ai_dashboard_agent import AIDashboardAgent
            output_path = ALLURE_REPORT.parent / "ai_dashboard_report.html"
            agent = AIDashboardAgent()
            agent.generate_dashboard_from_allure_results(
                allure_results_dir=ALLURE_RESULTS,
                output_path=output_path,
            )
            log.info("✅ AI Dashboard Generated Successfully")
            log.info("📊 Dashboard Location: %s", output_path)
        except Exception as exc:
            log.error("❌ Unexpected error while generating AI dashboard: %s", exc)

    @staticmethod
    def _copy_reports_to_project() -> None:
        """
        Copy allure-report, allure-results and AI dashboard from the temp
        ALLURE_REPORT/ALLURE_RESULTS location to the project testReport directory.

        Uses robocopy on Windows (handles MAX_PATH > 260) and shutil on other OS.
        Silently skips if source and destination are the same directory.
        """
        from pathlib import Path as _Path
        import subprocess as _subprocess

        # Project report root (derived from this file's location)
        project_root = _Path(__file__).resolve().parent.parent.parent
        project_report = project_root / "testReport" / "Execution_Backup" / "report"

        # If ALLURE_REPORT is already inside the project, nothing to copy
        try:
            ALLURE_REPORT.relative_to(project_report)
            log.debug("Reports already in project directory — skipping copy.")
            return
        except ValueError:
            pass  # ALLURE_REPORT is outside project — proceed with copy

        project_report.mkdir(parents=True, exist_ok=True)

        def _robocopy(src: _Path, dst: str) -> None:
            """Use robocopy on Windows for MAX_PATH-safe copying."""
            if os.name == "nt":
                result = _subprocess.run(
                    ["robocopy", str(src), dst, "/E", "/NFL", "/NDL", "/NJH", "/NJS"],
                    capture_output=True, text=True,
                )
                # robocopy exit codes 0-7 are success/info; 8+ are errors
                if result.returncode >= 8:
                    log.warning("robocopy warning (exit %d): %s", result.returncode, result.stderr)
            else:
                import shutil as _shutil
                dst_path = _Path(dst)
                if dst_path.exists():
                    _shutil.rmtree(dst_path)
                _shutil.copytree(str(src), dst)

        # Copy allure-report
        if ALLURE_REPORT.exists() and (ALLURE_REPORT / "index.html").exists():
            dst = str(project_report / "allure-report")
            _robocopy(ALLURE_REPORT, dst)
            log.info("📂 Allure report stored → %s", _Path(dst) / "index.html")

        # Copy allure-results
        if ALLURE_RESULTS.exists():
            dst = str(project_report / "allure-results")
            _robocopy(ALLURE_RESULTS, dst)
            log.info("📂 Allure results stored → %s", dst)

        # Copy AI dashboard (single file)
        ai_dash_src = ALLURE_REPORT.parent / "ai_dashboard_report.html"
        if ai_dash_src.exists():
            ai_dash_dst = project_report / "ai_dashboard_report.html"
            try:
                import shutil as _shutil
                _shutil.copy2(str(ai_dash_src), str(ai_dash_dst))
                log.info("📊 AI Dashboard stored → %s", ai_dash_dst)
            except Exception as exc:
                log.warning("Could not copy AI dashboard to project: %s", exc)

    # ── Allure attachment helpers (used by conftest.py page fixture) ──────────

    @staticmethod
    def attach_file_if_exists(path: Path, name: str, attachment_type) -> None:
        """
        Attach a file to the current Allure test result if it exists.

        Parameters
        ----------
        path            : Path   — file to attach
        name            : str    — attachment label shown in Allure
        attachment_type : allure.attachment_type — e.g. PNG, ZIP, MP4
        """
        import allure
        if path.exists():
            allure.attach.file(str(path), name=name, attachment_type=attachment_type)

    @staticmethod
    def cleanup_file(path: Path) -> None:
        """
        Delete a file silently (used to clean up passing-test artifacts).

        Parameters
        ----------
        path : Path — file to delete (no-op if it doesn't exist)
        """
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            log.debug("Could not clean up file %s: %s", path, exc)

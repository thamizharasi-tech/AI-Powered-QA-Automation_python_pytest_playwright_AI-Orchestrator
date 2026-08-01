"""
AI Dashboard Agent
==================
Generates a modern, self-contained HTML dashboard for QA execution reporting.

The output is designed for stakeholder review and can be opened directly in a browser.
It embeds CSS, JavaScript, and Chart.js for a polished single-file experience.

Python integration example:

    from jinja2 import Template

    template = Template("<h1>{{ report_title }}</h1>")
    html = template.render(
        report_title=report_title,
        environment=environment,
        execution_time=execution_time,
        summary=summary,
        tc_data=tc_data,
    )

Expected Python dictionary structure for the table rows:

    results = [
        {
            "tc_id": "TC_001",
            "description": "",
            "status": "Pass",
            "duration": 120,
            "phase_statuses": {},
            "details": {}
        }
    ]
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AIDashboardAgent:
    """Create a polished HTML test execution dashboard from structured QA data."""

    def __init__(self) -> None:
        self.template_name = "executive_dashboard.html"

    def build_payload(
        self,
        report_title: str,
        environment: str,
        execution_time: str,
        application_name: str,
        suite_name: str,
        summary: Optional[Dict[str, Any]] = None,
        tc_data: Optional[List[Dict[str, Any]]] = None,
        phase_summary: Optional[List[Dict[str, Any]]] = None,
        env_props: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        summary = summary or {}
        tc_data = tc_data or []
        phase_summary = phase_summary or []
        env_props = env_props or {}

        normalized_summary = {
            "total_tests": int(summary.get("total_tests", len(tc_data))),
            "passed": int(summary.get("passed", 0)),
            "failed": int(summary.get("failed", 0)),
            "skipped": int(summary.get("skipped", 0)),
            "pass_percentage": float(summary.get("pass_percentage", 0.0)),
            "total_duration": float(summary.get("total_duration", 0.0)),
        }

        if normalized_summary["total_tests"] == 0 and tc_data:
            normalized_summary["total_tests"] = len(tc_data)

        if normalized_summary["total_tests"] > 0 and normalized_summary["passed"] == 0 and normalized_summary["failed"] == 0 and normalized_summary["skipped"] == 0:
            normalized_summary["passed"] = sum(1 for item in tc_data if str(item.get("status", "")).lower().startswith("pass"))
            normalized_summary["failed"] = sum(1 for item in tc_data if str(item.get("status", "")).lower().startswith("fail"))
            normalized_summary["skipped"] = sum(1 for item in tc_data if str(item.get("status", "")).lower().startswith("skip"))
            normalized_summary["pass_percentage"] = round((normalized_summary["passed"] / normalized_summary["total_tests"]) * 100, 1) if normalized_summary["total_tests"] else 0.0

        # ── Quality gate: PASS ≥ 80%, WARN ≥ 60%, FAIL < 60% ─────────────────
        pct = normalized_summary["pass_percentage"]
        if pct >= 80:
            quality_gate = "PASS"
        elif pct >= 60:
            quality_gate = "WARN"
        else:
            quality_gate = "FAIL"

        return {
            "report_title": report_title,
            "environment": environment,
            "execution_time": execution_time,
            "application_name": application_name,
            "suite_name": suite_name,
            "summary": normalized_summary,
            "tc_data": tc_data,
            "phase_summary": phase_summary,
            "env_props": env_props,
            "quality_gate": quality_gate,
        }

    def generate_dashboard_html(
        self,
        output_path: Optional[Path | str] = None,
        report_title: str = "Executive QA Dashboard",
        environment: str = "QA",
        execution_time: str = "N/A",
        application_name: str = "Application Under Test",
        suite_name: str = "Automation Suite",
        summary: Optional[Dict[str, Any]] = None,
        tc_data: Optional[List[Dict[str, Any]]] = None,
        phase_summary: Optional[List[Dict[str, Any]]] = None,
    ) -> Path:
        payload = self.build_payload(
            report_title=report_title,
            environment=environment,
            execution_time=execution_time,
            application_name=application_name,
            suite_name=suite_name,
            summary=summary,
            tc_data=tc_data,
            phase_summary=phase_summary,
        )

        html_content = self._build_html(payload)

        if output_path is None:
            output_path = Path.cwd() / self.template_name
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    def generate_dashboard_from_allure_results(
        self,
        allure_results_dir: Path | str,
        output_path: Optional[Path | str] = None,
        report_title: str = "Executive QA Dashboard",
        environment: Optional[str] = None,
        execution_time: Optional[str] = None,
        application_name: str = "Application Under Test",
        suite_name: str = "Automation Suite",
    ) -> Path:
        results_dir = Path(allure_results_dir)
        if not results_dir.exists():
            raise FileNotFoundError(f"Allure results directory not found: {results_dir}")

        payload = self._build_payload_from_allure_results(results_dir)
        if environment:
            payload["environment"] = environment
        if not execution_time:
            execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Pass env_props so the Environment Info Strip is populated
        env_props = payload.get("env_props", {})

        # Build payload with env_props included
        full_payload = self.build_payload(
            report_title=report_title,
            environment=payload.get("environment", "QA"),
            execution_time=execution_time,
            application_name=application_name,
            suite_name=suite_name,
            summary=payload["summary"],
            tc_data=payload["tc_data"],
            phase_summary=payload["phase_summary"],
            env_props=env_props,
        )

        html_content = self._build_html(full_payload)

        if output_path is None:
            output_path = Path.cwd() / self.template_name
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    def _build_payload_from_allure_results(self, allure_results_dir: Path) -> Dict[str, Any]:
        env_props = self._load_environment_properties(allure_results_dir / "environment.properties")
        environment = env_props.get("Environment", "QA")
        tc_data: List[Dict[str, Any]] = []
        phase_counts: Dict[str, Dict[str, int]] = {}

        for result_file in sorted(allure_results_dir.glob("*-result.json")):
            try:
                result = json.loads(result_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue

            # ── Labels (multi-value: collect all values per name) ─────────────
            raw_labels = result.get("labels", [])
            labels_multi: Dict[str, List[str]] = {}
            for lbl in raw_labels:
                name = lbl.get("name", "")
                value = lbl.get("value", "")
                labels_multi.setdefault(name, []).append(value)
            # Flat labels dict (last value wins for duplicates)
            labels = {lbl.get("name"): lbl.get("value") for lbl in raw_labels}

            status = str(result.get("status", "unknown")).lower()
            status_display = status.capitalize() if status in {"passed", "failed", "skipped"} else "Failed"
            duration = 0.0
            if isinstance(result.get("start"), (int, float)) and isinstance(result.get("stop"), (int, float)):
                duration = round((result["stop"] - result["start"]) / 1000, 2)

            # Use the @allure.feature label as the phase/feature name
            feature = (labels_multi.get("feature") or [None])[-1] or labels.get("suite") or "General"
            # Use the last @allure.story label as the story
            story = (labels_multi.get("story") or [None])[-1] or result.get("name") or result.get("fullName", "")
            tc_id = result.get("testCaseId") or result.get("uuid") or result.get("fullName") or result.get("name")
            description = result.get("name") or str(result.get("fullName", tc_id))
            severity = labels.get("severity", "normal").upper()
            suite = labels.get("suite", "")
            sub_suite = labels.get("subSuite", "")
            parent_suite = labels.get("parentSuite", "")
            host = labels.get("host", "")
            framework = labels.get("framework", "pytest")

            # ── Steps extraction ──────────────────────────────────────────────
            steps_raw = result.get("steps", [])
            steps = []
            validation_results = []
            for step in steps_raw:
                step_status = str(step.get("status", "")).lower()
                step_duration = 0.0
                if isinstance(step.get("start"), (int, float)) and isinstance(step.get("stop"), (int, float)):
                    step_duration = round((step["stop"] - step["start"]) / 1000, 2)
                step_name = step.get("name", "")
                step_status_display = step_status.capitalize() if step_status in {"passed", "failed", "skipped"} else step_status
                steps.append({
                    "name": step_name,
                    "status": step_status_display,
                    "duration": step_duration,
                })
                # Each allure.step() is a validation checkpoint — collect as validation results
                if step_name:
                    icon = "[PASS]" if step_status == "passed" else ("[FAIL]" if step_status == "failed" else "[SKIP]")
                    validation_results.append(f"{icon} [{step_status_display}] {step_name}")

            # ── Attachments: read text logs and collect screenshot paths ───────
            logs = []
            screenshots = []
            error_messages = []
            for attachment in result.get("attachments", []):
                att_source = attachment.get("source", "")
                att_type = attachment.get("type", "")
                att_name = attachment.get("name", "")
                if not att_source:
                    continue

                if att_type == "text/plain":
                    att_path = allure_results_dir / att_source
                    if att_path.exists():
                        try:
                            content = att_path.read_text(encoding="utf-8").strip()
                            if content:
                                logs.append(f"[{att_name}] {content}")
                                # Extract validation lines from result() print output
                                for line in content.splitlines():
                                    line = line.strip()
                                    if not line:
                                        continue
                                    if line.startswith("Expected behaviour"):
                                        validation_results.append(f"[Expected] {line}")
                                    elif line.startswith("Actual behaviour"):
                                        is_fail = any(kw in line for kw in ("NOT", "failed", "error", "Error", "mismatch", "invalid"))
                                        icon = "[FAIL]" if is_fail else "[PASS]"
                                        validation_results.append(f"{icon} {line}")
                                        if is_fail:
                                            error_messages.append(line)
                        except Exception:
                            pass

                elif att_type in ("image/png", "image/jpeg", "image/gif"):
                    # Record screenshot attachment name and source filename
                    screenshots.append(f"{att_name} ({att_source})")

                elif att_type == "application/zip":
                    # Playwright trace zip
                    logs.append(f"[{att_name}] Playwright trace: {att_source}")

            # ── Status detail (statusDetails) ─────────────────────────────────
            status_details = result.get("statusDetails", {})
            if status_details.get("message"):
                error_messages.insert(0, status_details["message"])
            # Include stack trace in logs for failed tests
            if status_details.get("trace"):
                logs.append(f"[Stack Trace]\n{status_details['trace']}")

            tc_data.append(
                {
                    "tc_id": str(tc_id),
                    "description": description,
                    "status": status_display,
                    "duration": duration,
                    "phase_statuses": {feature: status_display},
                    "details": {
                        "story": story,
                        "feature": feature,
                        "severity": severity,
                        "suite": suite,
                        "sub_suite": sub_suite,
                        "parent_suite": parent_suite,
                        "host": host,
                        "framework": framework,
                        "full_name": result.get("fullName", ""),
                        "description": result.get("description", ""),
                        "labels": labels,
                        "steps": steps,
                        "validation_results": validation_results,
                        "screenshots": screenshots,
                        "logs": logs,
                        "error_messages": error_messages,
                        "result_uuid": result.get("uuid"),
                    },
                }
            )

            phase_counts.setdefault(feature, {"passed": 0, "failed": 0, "skipped": 0, "total": 0})
            phase_counts[feature]["total"] += 1
            if status == "passed":
                phase_counts[feature]["passed"] += 1
            elif status == "skipped":
                phase_counts[feature]["skipped"] += 1
            else:
                phase_counts[feature]["failed"] += 1

        summary = {
            "total_tests": len(tc_data),
            "passed": sum(1 for item in tc_data if item["status"] == "Passed"),
            "failed": sum(1 for item in tc_data if item["status"] == "Failed"),
            "skipped": sum(1 for item in tc_data if item["status"] == "Skipped"),
            "pass_percentage": round(
                (sum(1 for item in tc_data if item["status"] == "Passed") / len(tc_data)) * 100, 1
            ) if tc_data else 0.0,
            "total_duration": round(sum(item["duration"] for item in tc_data), 2),
        }

        phase_summary = [
            {
                "phase_name": phase,
                "passed": counts["passed"],
                "failed": counts["failed"],
                "skipped": counts["skipped"],
                "pass_percentage": round((counts["passed"] / counts["total"]) * 100, 1) if counts["total"] else 0.0,
            }
            for phase, counts in sorted(phase_counts.items())
        ]

        return {
            "environment": environment,
            "env_props": env_props,       # ← pass full props for Environment Info Strip
            "summary": summary,
            "tc_data": tc_data,
            "phase_summary": phase_summary,
        }

    def _load_environment_properties(self, path: Path) -> Dict[str, str]:
        if not path.exists():
            return {}

        properties: Dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()
        return properties

    def _build_html(self, payload: Dict[str, Any]) -> str:
        summary = payload["summary"]
        tc_data = payload["tc_data"]
        phase_summary = payload["phase_summary"]
        env_props = payload.get("env_props", {})
        quality_gate = payload.get("quality_gate", "PASS")

        # ── Safe JSON embedding ───────────────────────────────────────────────
        # Replace < > & with Unicode escapes so that XSS payloads stored in
        # test names / step names / error messages cannot execute as HTML when
        # the JSON is embedded inside a <script> block.
        # This is the same technique used by Django, Flask, and React.
        def _safe_json(obj) -> str:
            return (
                json.dumps(obj, indent=2)
                .replace("<", r"\u003c")
                .replace(">", r"\u003e")
                .replace("&", r"\u0026")
            )

        tc_json = _safe_json(tc_data)
        summary_json = _safe_json(summary)
        phase_json = _safe_json(phase_summary)
        env_props_json = _safe_json(env_props)

        # ── Quality gate colours ───────────────────────────────────────────────
        gate_color = {"PASS": "#2fbf71", "WARN": "#f59e0b", "FAIL": "#ef4444"}.get(quality_gate, "#2fbf71")
        gate_icon  = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}.get(quality_gate, "✅")
        gate_label = {"PASS": "Quality Gate: PASSED", "WARN": "Quality Gate: WARNING", "FAIL": "Quality Gate: FAILED"}.get(quality_gate, "Quality Gate: PASSED")

        # ── Environment info strip ─────────────────────────────────────────────
        env_items = []
        for key in ("Platform", "Python", "Framework", "Browser", "Headless"):
            val = env_props.get(key, "")
            if val:
                env_items.append(f'<span class="env-item"><strong>{key}:</strong> {val}</span>')
        env_strip_html = "".join(env_items) if env_items else '<span class="env-item"><strong>Environment:</strong> __ENVIRONMENT__</span>'

        template = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>__REPORT_TITLE__</title>
  <!-- Chart.js v4.4.3 — https://www.chartjs.org -->
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js\"></script>
  <style>
    :root {
      --bg: #f4f7fb; --surface: #ffffff; --surface-2: #f8fbff;
      --primary: #2557d6; --primary-2: #163a8d;
      --success: #2fbf71; --danger: #ef4444; --warning: #f59e0b; --neutral: #64748b;
      --text: #14213d; --muted: #64748b; --border: #e5ebf1;
      --shadow: 0 12px 30px rgba(20,33,61,0.08);
    }
    body.dark {
      --bg: #07111f; --surface: #101a2c; --surface-2: #14233a;
      --primary: #7dd3fc; --primary-2: #38bdf8;
      --success: #34d399; --danger: #f87171; --warning: #fbbf24; --neutral: #94a3b8;
      --text: #f8fafc; --muted: #cbd5e1; --border: #283549;
      --shadow: 0 12px 30px rgba(2,8,23,0.4);
    }
    * { box-sizing: border-box; }
    body { margin:0; font-family:Inter,Segoe UI,Roboto,Arial,sans-serif; background:linear-gradient(180deg,var(--bg) 0%,#eef4ff 100%); color:var(--text); transition:background 0.2s,color 0.2s; }
    .container { max-width:1440px; margin:0 auto; padding:24px; }
    /* ── Header ── */
    .header { background:linear-gradient(135deg,var(--primary),var(--primary-2)); color:white; border-radius:24px; padding:28px; box-shadow:var(--shadow); }
    .header-top { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; flex-wrap:wrap; }
    .title-block h1 { margin:0 0 6px; font-size:28px; font-weight:800; }
    .title-block .subtitle { margin:0; opacity:0.9; font-size:14px; line-height:1.6; }
    .controls { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
    .pill { display:inline-flex; align-items:center; gap:6px; padding:7px 12px; border-radius:999px; background:rgba(255,255,255,0.16); font-size:13px; }
    /* ── Quality Gate Banner ── */
    .quality-gate { margin-top:16px; display:flex; align-items:center; gap:12px; padding:12px 18px; border-radius:14px; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.2); }
    .gate-badge { font-size:22px; font-weight:900; letter-spacing:0.04em; }
    .gate-info { flex:1; }
    .gate-info .gate-title { font-size:15px; font-weight:700; }
    .gate-info .gate-sub { font-size:12px; opacity:0.85; margin-top:2px; }
    .gate-bar-wrap { width:200px; height:8px; background:rgba(255,255,255,0.2); border-radius:999px; overflow:hidden; }
    .gate-bar { height:100%; border-radius:999px; transition:width 0.6s ease; }
    /* ── Env Strip ── */
    .env-strip { margin-top:14px; display:flex; flex-wrap:wrap; gap:8px; padding:10px 14px; background:rgba(255,255,255,0.08); border-radius:12px; border:1px solid rgba(255,255,255,0.12); }
    .env-item { font-size:12px; color:rgba(255,255,255,0.9); }
    .env-item strong { color:white; }
    /* ── Buttons ── */
    button,select,input { font:inherit; }
    .btn { border:none; border-radius:12px; padding:9px 14px; cursor:pointer; transition:transform 0.15s,box-shadow 0.15s,background 0.2s; font-weight:600; font-size:13px; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 8px 16px rgba(0,0,0,0.12); }
    .btn-dark { background:var(--surface); color:var(--text); }
    .btn-primary { background:white; color:var(--primary); }
    .btn-secondary { background:rgba(255,255,255,0.16); color:white; border:1px solid rgba(255,255,255,0.22); }
    .btn-success { background:var(--success); color:white; }
    .btn-danger { background:var(--danger); color:white; }
    .btn-warning { background:var(--warning); color:white; }
    .btn-active { outline:2px solid rgba(255,255,255,0.5); box-shadow:inset 0 0 0 1px rgba(255,255,255,0.3); }
    /* ── Cards ── */
    .card { background:var(--surface); border:1px solid var(--border); border-radius:20px; padding:18px; box-shadow:var(--shadow); }
    .card h3 { margin:0 0 8px; font-size:13px; color:var(--muted); font-weight:700; text-transform:uppercase; letter-spacing:0.05em; }
    .card .value { font-size:32px; font-weight:800; }
    .card .sub { margin-top:4px; color:var(--muted); font-size:12px; }
    /* ── Stats grid ── */
    .stats-grid { margin-top:20px; display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); }
    .stat-card-passed .value { color:var(--success); }
    .stat-card-failed .value { color:var(--danger); }
    .stat-card-skipped .value { color:var(--neutral); }
    .stat-card-rate .value { color:var(--primary); }
    /* ── Progress bar ── */
    .progress-wrap { margin-top:8px; height:6px; background:var(--border); border-radius:999px; overflow:hidden; }
    .progress-bar { height:100%; border-radius:999px; }
    /* ── Grid layouts ── */
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:18px; }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-top:18px; }
    .chart-card { min-height:320px; }
    /* ── Phase cards ── */
    .summary-grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); margin-top:16px; }
    .phase-card { border:1px solid var(--border); border-radius:16px; padding:16px; background:var(--surface); }
    .phase-card h4 { margin:0 0 10px; font-size:14px; font-weight:700; }
    .phase-stat-row { display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px; }
    /* ── Top failures ── */
    .failure-row { display:flex; gap:12px; align-items:flex-start; padding:10px 12px; border-radius:10px; background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.15); margin-bottom:8px; }
    .failure-rank { font-size:18px; font-weight:800; color:var(--danger); min-width:28px; }
    .failure-info { flex:1; }
    .failure-name { font-size:13px; font-weight:600; }
    .failure-meta { font-size:12px; color:var(--muted); margin-top:2px; }
    /* ── Severity breakdown ── */
    .sev-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:10px; margin-top:12px; }
    .sev-card { text-align:center; padding:12px 8px; border-radius:12px; border:1px solid var(--border); }
    .sev-card .sev-count { font-size:24px; font-weight:800; }
    .sev-card .sev-label { font-size:11px; color:var(--muted); text-transform:uppercase; margin-top:2px; }
    /* ── Filters & table ── */
    .filters { display:grid; gap:10px; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); margin:18px 0 10px; }
    .filters input,.filters select { width:100%; padding:9px 12px; border-radius:10px; border:1px solid var(--border); background:var(--surface); color:var(--text); font-size:13px; }
    .table-wrap { overflow-x:auto; margin-top:12px; }
    table { width:100%; border-collapse:collapse; background:var(--surface); border-radius:16px; overflow:hidden; }
    th,td { padding:11px 14px; border-bottom:1px solid var(--border); text-align:left; vertical-align:top; }
    th { background:var(--surface-2); color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:0.04em; }
    tr:hover { background:rgba(37,87,214,0.03); }
    /* ── Badges & tags ── */
    .status-badge { display:inline-flex; padding:5px 10px; border-radius:999px; font-weight:700; font-size:12px; }
    .status-pass { background:rgba(47,191,113,0.15); color:var(--success); }
    .status-fail { background:rgba(239,68,68,0.14); color:var(--danger); }
    .status-skip { background:rgba(100,116,139,0.16); color:var(--neutral); }
    .tag { display:inline-block; border-radius:999px; padding:5px 10px; margin:3px 4px 0 0; font-size:12px; background:rgba(37,87,214,0.1); color:var(--primary); }
    .phase-chip { display:inline-flex; align-items:center; gap:6px; padding:6px 10px; border-radius:999px; font-size:12px; background:rgba(20,33,61,0.06); }
    /* ── Detail panel ── */
    .detail-panel { margin-top:12px; border:1px solid var(--border); border-radius:16px; padding:18px; background:var(--surface-2); display:none; }
    .muted { color:var(--muted); }
    /* ── Toast ── */
    .toast { position:fixed; right:20px; bottom:20px; padding:12px 18px; border-radius:999px; background:var(--text); color:white; box-shadow:var(--shadow); opacity:0; transform:translateY(8px); transition:all 0.2s; pointer-events:none; z-index:999; }
    .toast.show { opacity:1; transform:translateY(0); }
    .empty-state { padding:24px; text-align:center; color:var(--muted); }
    @media(max-width:900px) {
      .grid-2,.grid-3 { grid-template-columns:1fr; }
      .header-top { flex-direction:column; }
      .gate-bar-wrap { display:none; }
    }
  </style>
</head>
<body>
  <div class=\"container\">

    <!-- ══ HEADER ══════════════════════════════════════════════════════════ -->
    <header class=\"header\">
      <div class=\"header-top\">
        <div class=\"title-block\">
          <h1>__REPORT_TITLE__</h1>
          <p class=\"subtitle\">
            <strong>__APPLICATION_NAME__</strong> &nbsp;|&nbsp;
            <strong>__SUITE_NAME__</strong> &nbsp;|&nbsp;
            <strong>__ENVIRONMENT__</strong> &nbsp;|&nbsp;
            __EXECUTION_TIME__
          </p>
        </div>
        <div class=\"controls\">
          <button class=\"btn btn-dark\" id=\"theme-toggle\">Dark Mode</button>
          <button class=\"btn btn-primary\" id=\"download-report\">Download</button>
        </div>
      </div>

      <!-- Quality Gate Banner -->
      <div class=\"quality-gate\" id=\"quality-gate-banner\">
        <span class=\"gate-badge\" id=\"gate-icon\">__GATE_ICON__</span>
        <div class=\"gate-info\">
          <div class=\"gate-title\" id=\"gate-label\">__GATE_LABEL__</div>
          <div class=\"gate-sub\">Threshold: PASS ≥ 80% &nbsp;|&nbsp; WARN ≥ 60% &nbsp;|&nbsp; FAIL &lt; 60%</div>
        </div>
        <div class=\"gate-bar-wrap\">
          <div class=\"gate-bar\" id=\"gate-bar\" style=\"background:__GATE_COLOR__;width:0%;\"></div>
        </div>
      </div>

      <!-- Environment Info Strip -->
      <div class=\"env-strip\">__ENV_STRIP__</div>
    </header>

    <!-- ══ KPI CARDS ════════════════════════════════════════════════════════ -->
    <section class=\"stats-grid\">
      <article class=\"card\">
        <h3>Total Tests</h3>
        <div class=\"value\" id=\"total-tests\">0</div>
        <div class=\"sub\">All discovered test cases</div>
      </article>
      <article class=\"card stat-card-passed\">
        <h3>Passed</h3>
        <div class=\"value\" id=\"passed-count\">0</div>
        <div class=\"sub\">Successful executions</div>
        <div class=\"progress-wrap\"><div class=\"progress-bar\" id=\"pass-bar\" style=\"background:var(--success);width:0%;\"></div></div>
      </article>
      <article class=\"card stat-card-failed\">
        <h3>Failed</h3>
        <div class=\"value\" id=\"failed-count\">0</div>
        <div class=\"sub\">Needs immediate action</div>
        <div class=\"progress-wrap\"><div class=\"progress-bar\" id=\"fail-bar\" style=\"background:var(--danger);width:0%;\"></div></div>
      </article>
      <article class=\"card stat-card-skipped\">
        <h3>Skipped</h3>
        <div class=\"value\" id=\"skipped-count\">0</div>
        <div class=\"sub\">Deferred or not executed</div>
      </article>
      <article class=\"card stat-card-rate\">
        <h3>Pass Rate</h3>
        <div class=\"value\" id=\"pass-rate\">0%</div>
        <div class=\"sub\">Quality performance indicator</div>
        <div class=\"progress-wrap\"><div class=\"progress-bar\" id=\"rate-bar\" style=\"background:var(--primary);width:0%;\"></div></div>
      </article>
      <article class=\"card\">
        <h3>Total Duration</h3>
        <div class=\"value\" id=\"total-duration\">0s</div>
        <div class=\"sub\">Combined runtime</div>
      </article>
    </section>

    <!-- ══ CHARTS ═══════════════════════════════════════════════════════════ -->
    <section class=\"grid-2\">
      <article class=\"card chart-card\">
        <h3>Pass vs Fail Distribution</h3>
        <canvas id=\"status-chart\"></canvas>
      </article>
      <article class=\"card chart-card\">
        <h3>Phase-wise Execution Status</h3>
        <canvas id=\"phase-chart\"></canvas>
      </article>
    </section>

    <!-- ══ PHASE SUMMARY ════════════════════════════════════════════════════ -->
    <section class=\"card\" style=\"margin-top:18px;\">
      <h3>Phase / Feature Summary</h3>
      <div class=\"summary-grid\" id=\"phase-summary\"></div>
    </section>

    <!-- ══ TOP FAILURES + SEVERITY ══════════════════════════════════════════ -->
    <section class=\"grid-2\">
      <article class=\"card\" style=\"margin-top:18px;\">
        <h3>Top Failed Tests</h3>
        <div id=\"top-failures\"><div class=\"empty-state muted\">No failures — all tests passed.</div></div>
      </article>
      <article class=\"card\" style=\"margin-top:18px;\">
        <h3>Severity Breakdown</h3>
        <div class=\"sev-grid\" id=\"severity-grid\"></div>
      </article>
    </section>

    <!-- ══ TEST RESULTS TABLE ════════════════════════════════════════════════ -->
    <section class=\"card\" style=\"margin-top:18px;\">
      <h3>Advanced Filters &amp; Test Results</h3>
      <div class=\"filters\">
        <input id=\"filter-id\" type=\"text\" placeholder=\"Filter by Test Case ID\" />
        <select id=\"filter-status\">
          <option value=\"all\">All Status</option>
          <option value=\"passed\">Passed</option>
          <option value=\"failed\">Failed</option>
          <option value=\"skipped\">Skipped</option>
        </select>
        <select id=\"filter-phase\"><option value=\"all\">All Phases</option></select>
        <select id=\"filter-severity\">
          <option value=\"all\">All Severities</option>
          <option value=\"CRITICAL\">Critical</option>
          <option value=\"NORMAL\">Normal</option>
          <option value=\"MINOR\">Minor</option>
          <option value=\"BLOCKER\">Blocker</option>
          <option value=\"TRIVIAL\">Trivial</option>
        </select>
        <input id=\"search-box\" type=\"text\" placeholder=\"Search description\" />
        <select id=\"sort-by\">
          <option value=\"duration\">Sort: Duration ↓</option>
          <option value=\"status\">Sort: Status</option>
          <option value=\"severity\">Sort: Severity</option>
        </select>
      </div>
      <div style=\"display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;\">
        <button class=\"btn btn-danger\" type=\"button\" id=\"failed-filter\">Failed Test Quick Filter</button>
        <button class=\"btn btn-secondary\" type=\"button\" id=\"reset-filters\">Reset Filters</button>
        <button class=\"btn btn-dark\" type=\"button\" id=\"copy-errors\">Copy Error Details</button>
        <button class=\"btn btn-success\" type=\"button\" id=\"export-csv\">Export to CSV</button>
        <button class=\"btn btn-warning\" type=\"button\" id=\"export-excel\">Export to Excel</button>
      </div>
      <div class=\"muted\" id=\"filter-summary\" style=\"font-size:13px;margin-bottom:8px;\">Loading results...</div>
      <div class=\"table-wrap\">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Test Case ID</th>
              <th>Description</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Feature / Phase</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody id=\"results-table\"></tbody>
        </table>
      </div>
    </section>

  </div>

  <script>
    const TC_DATA = __TC_JSON__;
    const SUMMARY = __SUMMARY_JSON__;
    const PHASE_SUMMARY = __PHASE_JSON__;

    const state = {
      query: '',
      status: 'all',
      phase: 'all',
      severity: 'all',
      sortBy: 'duration',
      idFilter: '',
      failedOnly: false,
      selectedRow: null,
      darkMode: false,
    };

    const SEV_ORDER = { BLOCKER: 0, CRITICAL: 1, NORMAL: 2, MINOR: 3, TRIVIAL: 4 };

    function statusClass(status) {
      const normalized = String(status || '').toLowerCase();
      if (normalized === 'pass' || normalized === 'passed') return 'status-pass';
      if (normalized === 'fail' || normalized === 'failed') return 'status-fail';
      return 'status-skip';
    }

    function showToast(message, tone = 'info') {
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.className = 'toast show';
      toast.style.background = tone === 'success' ? '#2fbf71' : tone === 'danger' ? '#ef4444' : '#14213d';
      clearTimeout(showToast.timeout);
      showToast.timeout = setTimeout(() => toast.className = 'toast', 2200);
    }

    function renderSummary() {
      const total = SUMMARY.total_tests ?? 0;
      const passed = SUMMARY.passed ?? 0;
      const failed = SUMMARY.failed ?? 0;
      const pct = Math.round((SUMMARY.pass_percentage ?? 0) * 10) / 10;
      document.getElementById('total-tests').textContent = total;
      document.getElementById('passed-count').textContent = passed;
      document.getElementById('failed-count').textContent = failed;
      document.getElementById('skipped-count').textContent = SUMMARY.skipped ?? 0;
      document.getElementById('pass-rate').textContent = `${pct}%`;
      document.getElementById('total-duration').textContent = `${SUMMARY.total_duration ?? 0}s`;
      // Progress bars
      if (total > 0) {
        document.getElementById('pass-bar').style.width = `${(passed/total)*100}%`;
        document.getElementById('fail-bar').style.width = `${(failed/total)*100}%`;
        document.getElementById('rate-bar').style.width = `${pct}%`;
      }
      // Quality gate bar animation
      setTimeout(() => {
        const bar = document.getElementById('gate-bar');
        if (bar) bar.style.width = `${Math.min(pct, 100)}%`;
      }, 300);
    }

    function getFilteredRows() {
      return TC_DATA.filter((row) => {
        const status = String(row.status || '').toLowerCase();
        const description = String(row.description || '').toLowerCase();
        const id = String(row.tc_id || '').toLowerCase();
        const sev = String((row.details && row.details.severity) || '').toUpperCase();
        const phaseMatch = state.phase === 'all' || Object.keys(row.phase_statuses || {}).includes(state.phase);
        const idMatch = state.idFilter === '' || id.includes(state.idFilter.toLowerCase());
        const statusMatch = state.status === 'all' || status === state.status;
        const queryMatch = state.query === '' || description.includes(state.query.toLowerCase());
        const failedMatch = !state.failedOnly || status === 'failed' || status === 'fail';
        const sevMatch = state.severity === 'all' || sev === state.severity;
        return idMatch && statusMatch && queryMatch && phaseMatch && failedMatch && sevMatch;
      }).sort((a, b) => {
        if (state.sortBy === 'status') return String(a.status||'').localeCompare(String(b.status||''));
        if (state.sortBy === 'severity') {
          const sa = SEV_ORDER[String((a.details&&a.details.severity)||'NORMAL').toUpperCase()] ?? 99;
          const sb = SEV_ORDER[String((b.details&&b.details.severity)||'NORMAL').toUpperCase()] ?? 99;
          return sa - sb;
        }
        return (Number(b.duration) || 0) - (Number(a.duration) || 0);
      });
    }

    function updateFilterSummary() {
      const rows = getFilteredRows();
      document.getElementById('filter-summary').textContent =
        `${rows.length} result${rows.length === 1 ? '' : 's'} shown with the current filters.`;
    }

    function renderTable() {
      const rows = getFilteredRows();
      const table = document.getElementById('results-table');
      table.innerHTML = '';
      updateFilterSummary();
      if (!rows.length) {
        table.innerHTML = '<tr><td colspan="8" class="empty-state">No matching records found.</td></tr>';
        return;
      }
      rows.forEach((row, idx) => {
        const d = row.details || {};
        const sev = d.severity || 'NORMAL';
        const sevColor = sev === 'CRITICAL' || sev === 'BLOCKER' ? 'var(--danger)' : sev === 'MINOR' || sev === 'TRIVIAL' ? 'var(--neutral)' : 'var(--warning)';
        const feature = d.feature || Object.keys(row.phase_statuses || {})[0] || '—';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="color:var(--muted);font-size:12px;">${idx + 1}</td>
          <td><strong style="font-size:13px;">${row.tc_id}</strong></td>
          <td style="font-size:13px;max-width:280px;">${row.description || 'N/A'}</td>
          <td><span style="font-size:11px;font-weight:700;color:${sevColor};">${sev}</span></td>
          <td><span class=\"status-badge ${statusClass(row.status)}\">${row.status}</span></td>
          <td style="font-size:13px;color:var(--muted);">${row.duration ?? 0}s</td>
          <td style="font-size:12px;">${feature}</td>
          <td><button class=\"btn btn-primary\" type=\"button\" style=\"padding:6px 12px;font-size:12px;\" data-id=\"${row.tc_id}\">Details</button></td>
        `;
        tr.querySelector('button').addEventListener('click', () => renderDetails(row));
        table.appendChild(tr);
      });
    }

    function renderTopFailures() {
      const container = document.getElementById('top-failures');
      const failed = TC_DATA.filter(r => String(r.status||'').toLowerCase().startsWith('fail'))
        .sort((a,b) => (Number(b.duration)||0) - (Number(a.duration)||0))
        .slice(0, 5);
      if (!failed.length) {
        container.innerHTML = '<div class="empty-state muted" style="padding:16px;">✅ No failures — all tests passed!</div>';
        return;
      }
      container.innerHTML = failed.map((row, i) => {
        const d = row.details || {};
        const firstErr = (d.error_messages || [])[0] || '';
        return `<div class="failure-row">
          <div class="failure-rank">#${i+1}</div>
          <div class="failure-info">
            <div class="failure-name">${row.tc_id} — ${row.description || ''}</div>
            <div class="failure-meta">
              ${d.feature ? `${d.feature}` : ''} ${d.severity ? `&nbsp;${d.severity}` : ''} &nbsp;⏱ ${row.duration??0}s
            </div>
            ${firstErr ? `<div style="font-size:12px;color:var(--danger);margin-top:4px;padding:4px 8px;background:rgba(239,68,68,0.06);border-radius:6px;">${firstErr}</div>` : ''}
          </div>
        </div>`;
      }).join('');
    }

    function renderSeverityBreakdown() {
      const container = document.getElementById('severity-grid');
      const sevMap = {};
      TC_DATA.forEach(row => {
        const sev = String((row.details && row.details.severity) || 'NORMAL').toUpperCase();
        sevMap[sev] = (sevMap[sev] || 0) + 1;
      });
      const sevDefs = [
        { key: 'BLOCKER',  icon: 'BLK', color: '#7c3aed' },
        { key: 'CRITICAL', icon: 'CRT', color: 'var(--danger)' },
        { key: 'NORMAL',   icon: 'NRM', color: 'var(--warning)' },
        { key: 'MINOR',    icon: 'MNR', color: 'var(--primary)' },
        { key: 'TRIVIAL',  icon: 'TRV', color: 'var(--neutral)' },
      ];
      container.innerHTML = sevDefs.map(s => `
        <div class="sev-card">
          <div class="sev-count" style="color:${s.color};">${sevMap[s.key] || 0}</div>
          <div class="sev-label">${s.icon} ${s.key}</div>
        </div>`).join('');
    }

    function renderDetails(row) {
      state.selectedRow = row;

      // Remove any existing detail panel
      const current = document.querySelector('.detail-panel');
      if (current) {
        if (current.dataset.tcId === String(row.tc_id)) { current.remove(); return; }
        current.remove();
      }

      const detailPanel = document.createElement('div');
      detailPanel.className = 'detail-panel';
      detailPanel.dataset.tcId = String(row.tc_id);
      detailPanel.style.display = 'block';

      const d = row.details || {};
      const steps = d.steps || [];
      const logs = d.logs || [];
      const errors = d.error_messages || [];
      const validations = d.validation_results || [];
      const screenshots = d.screenshots || [];
      const labels = d.labels || {};

      // ── Status colour bar ──────────────────────────────────────────────────
      const statusColor = (s) => {
        const n = String(s||'').toLowerCase();
        if (n==='passed'||n==='pass') return 'var(--success)';
        if (n==='failed'||n==='fail') return 'var(--danger)';
        return 'var(--neutral)';
      };

      // ── Section helper ─────────────────────────────────────────────────────
      const section = (icon, title, count, content, accentColor='var(--primary)') => `
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:0;">
          <div style="display:flex;align-items:center;gap:8px;padding:10px 14px;background:var(--surface-2);border-bottom:1px solid var(--border);">
            <span style="font-size:16px;">${icon}</span>
            <span style="font-weight:700;font-size:13px;color:var(--text);">${title}</span>
            ${count !== null ? `<span style="margin-left:auto;background:${accentColor};color:white;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;">${count}</span>` : ''}
          </div>
          <div style="padding:12px 14px;">${content}</div>
        </div>`;

      // ── Steps table ────────────────────────────────────────────────────────
      const stepsContent = steps.length
        ? `<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr>
              <th style="text-align:left;padding:6px 10px;background:var(--surface-2);border-bottom:1px solid var(--border);color:var(--muted);font-size:11px;text-transform:uppercase;">#</th>
              <th style="text-align:left;padding:6px 10px;background:var(--surface-2);border-bottom:1px solid var(--border);color:var(--muted);font-size:11px;text-transform:uppercase;">Step Name</th>
              <th style="text-align:left;padding:6px 10px;background:var(--surface-2);border-bottom:1px solid var(--border);color:var(--muted);font-size:11px;text-transform:uppercase;">Status</th>
              <th style="text-align:left;padding:6px 10px;background:var(--surface-2);border-bottom:1px solid var(--border);color:var(--muted);font-size:11px;text-transform:uppercase;">Duration</th>
            </tr></thead>
            <tbody>${steps.map((s, i) => `
              <tr style="background:${i%2===0?'transparent':'rgba(37,87,214,0.02)'}">
                <td style="padding:7px 10px;border-bottom:1px solid var(--border);color:var(--muted);font-size:12px;">${i+1}</td>
                <td style="padding:7px 10px;border-bottom:1px solid var(--border);font-size:13px;">${s.name||''}</td>
                <td style="padding:7px 10px;border-bottom:1px solid var(--border);"><span class="status-badge ${statusClass(s.status)}">${s.status||'N/A'}</span></td>
                <td style="padding:7px 10px;border-bottom:1px solid var(--border);color:var(--muted);font-size:12px;">${s.duration??0}s</td>
              </tr>`).join('')}
            </tbody></table></div>`
        : '<span class="muted" style="font-size:13px;">⏭ No steps recorded for this test</span>';

      // ── Validation results ─────────────────────────────────────────────────
      const validationContent = validations.length
        ? `<div style="display:flex;flex-direction:column;gap:4px;">${validations.map(v => {
            const isPass = v.startsWith('✅');
            const isFail = v.startsWith('❌');
            const bg = isPass ? 'rgba(47,191,113,0.08)' : isFail ? 'rgba(239,68,68,0.08)' : 'rgba(100,116,139,0.06)';
            const border = isPass ? 'rgba(47,191,113,0.3)' : isFail ? 'rgba(239,68,68,0.3)' : 'rgba(100,116,139,0.2)';
            return `<div style="font-size:13px;padding:6px 10px;border-radius:8px;background:${bg};border-left:3px solid ${border};line-height:1.5;">${v}</div>`;
          }).join('')}</div>`
        : '<span class="muted" style="font-size:13px;">No validation results recorded</span>';

      // ── Error messages ─────────────────────────────────────────────────────
      const errorsContent = errors.length
        ? `<div style="display:flex;flex-direction:column;gap:6px;">${errors.map(e =>
            `<div style="display:flex;gap:8px;align-items:flex-start;padding:8px 10px;background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:8px;">
              
              <span style="color:var(--danger);font-size:13px;line-height:1.5;">${e}</span>
            </div>`).join('')}</div>`
        : '<div style="display:flex;gap:8px;align-items:center;padding:8px 10px;background:rgba(47,191,113,0.08);border:1px solid rgba(47,191,113,0.25);border-radius:8px;"><span style="color:var(--success);font-size:13px;font-weight:600;">No errors or warnings</span></div>';

      // ── Logs ───────────────────────────────────────────────────────────────
      const logsContent = logs.length
        ? `<pre style="margin:0;white-space:pre-wrap;word-break:break-word;font-size:12px;font-family:'Cascadia Code','Fira Code',monospace;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:12px;max-height:220px;overflow-y:auto;line-height:1.6;">${logs.join('\\n\\n---\\n\\n')}</pre>`
        : '<span class="muted" style="font-size:13px;">No execution logs captured</span>';

      // ── Screenshots ────────────────────────────────────────────────────────
      const screenshotsContent = screenshots.length
        ? `<div style="display:flex;flex-direction:column;gap:6px;">${screenshots.map(s =>
            `<div style="display:flex;gap:8px;align-items:center;padding:7px 10px;background:rgba(37,87,214,0.06);border:1px solid rgba(37,87,214,0.15);border-radius:8px;">
              
              <span style="font-size:13px;color:var(--primary);">${s}</span>
            </div>`).join('')}</div>`
        : '<span class="muted" style="font-size:13px;">No screenshots attached (screenshots are captured on failure only)</span>';

      // ── Compact metadata strip (Feature, Story, Severity, Suite only) ──────
      const metaStrip = [
        d.feature      ? `<span style="display:inline-flex;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;background:rgba(37,87,214,0.08);color:var(--primary);border:1px solid rgba(37,87,214,0.15);"><strong>Feature:</strong>&nbsp;${d.feature}</span>` : '',
        d.story        ? `<span style="display:inline-flex;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;background:rgba(37,87,214,0.08);color:var(--primary);border:1px solid rgba(37,87,214,0.15);"><strong>Story:</strong>&nbsp;${d.story}</span>` : '',
        d.severity     ? `<span style="display:inline-flex;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;background:rgba(245,158,11,0.1);color:var(--warning);border:1px solid rgba(245,158,11,0.2);"><strong>Severity:</strong>&nbsp;${d.severity}</span>` : '',
        d.suite        ? `<span style="display:inline-flex;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;background:rgba(100,116,139,0.08);color:var(--muted);border:1px solid var(--border);"><strong>Suite:</strong>&nbsp;${d.suite}</span>` : '',
      ].filter(Boolean).join('');

      // ── Header status bar ──────────────────────────────────────────────────
      const headerTags = [
        `<span class="status-badge ${statusClass(row.status)}">${row.status}</span>`,
        d.severity ? `<span class="tag" style="background:rgba(245,158,11,0.12);color:var(--warning);">🔥 ${d.severity}</span>` : '',
        d.feature  ? `<span class="tag">📦 ${d.feature}</span>` : '',
        d.story    ? `<span class="tag">📖 ${d.story}</span>` : '',
        `<span class="tag">⏱ ${row.duration??0}s</span>`,
      ].filter(Boolean).join('');

      detailPanel.innerHTML = `
        <!-- ── Panel header ── -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px;padding-bottom:16px;border-bottom:2px solid ${statusColor(row.status)}22;">
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <span style="width:6px;height:32px;border-radius:3px;background:${statusColor(row.status)};flex-shrink:0;display:inline-block;"></span>
              <h4 style="margin:0;font-size:16px;font-weight:700;line-height:1.3;word-break:break-word;">${row.description || row.tc_id}</h4>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;padding-left:16px;margin-bottom:6px;">${headerTags}</div>
            ${metaStrip ? `<div style="display:flex;gap:6px;flex-wrap:wrap;padding-left:16px;">${metaStrip}</div>` : ''}
          </div>
          <button class="btn btn-secondary" id="close-detail-panel" type="button" style="padding:6px 14px;font-size:13px;flex-shrink:0;">✕ Close</button>
        </div>

        ${d.description ? `
        <div style="margin-bottom:16px;padding:12px 14px;background:rgba(37,87,214,0.05);border:1px solid rgba(37,87,214,0.15);border-radius:10px;border-left:4px solid var(--primary);">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--primary);margin-bottom:6px;letter-spacing:0.05em;">📋 Test Description</div>
          <pre style="margin:0;white-space:pre-wrap;font-size:13px;font-family:inherit;color:var(--text);line-height:1.6;">${d.description}</pre>
        </div>` : ''}

        <!-- ── Quick stats row ── -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:16px;">
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:${statusColor(row.status)};">${row.status}</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Status</div>
          </div>
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:var(--primary);">${row.duration??0}s</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Duration</div>
          </div>
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:var(--text);">${steps.length}</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Steps</div>
          </div>
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:${errors.length?'var(--danger)':'var(--success)'};">${errors.length||'0'}</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Errors</div>
          </div>
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:var(--text);">${validations.length}</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Validations</div>
          </div>
          <div style="text-align:center;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;">
            <div style="font-size:18px;font-weight:800;color:var(--text);">${screenshots.length||'—'}</div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-top:2px;">Screenshots</div>
          </div>
        </div>

        <!-- ── Main content grid ── -->
        <div style="display:grid;gap:12px;">

          <!-- Steps (full width) -->
          ${section('', 'Test Steps', steps.length, stepsContent, 'var(--primary)')}

          <!-- Errors + Validations -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            ${section('', 'Error / Warning Messages', errors.length || null, errorsContent, errors.length ? 'var(--danger)' : 'var(--success)')}
            ${section('', 'Validation Results', validations.length, validationContent, 'var(--success)')}
          </div>

          <!-- Logs + Screenshots -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            ${section('', 'Execution Logs', logs.length || null, logsContent, 'var(--neutral)')}
            ${section('', 'Screenshots', screenshots.length || null, screenshotsContent, 'var(--warning)')}
          </div>

        </div>
      `;

      document.querySelector('table').insertAdjacentElement('afterend', detailPanel);
      detailPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      document.getElementById('close-detail-panel').addEventListener('click', () => detailPanel.remove());
    }

    function renderPhaseSummary() {
      const container = document.getElementById('phase-summary');
      container.innerHTML = '';
      if (!(PHASE_SUMMARY || []).length) {
        container.innerHTML = '<div class="muted" style="padding:12px;font-size:13px;">No phase data available.</div>';
        return;
      }
      (PHASE_SUMMARY || []).forEach((phase) => {
        const pct = phase.pass_percentage ?? 0;
        const barColor = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
        const total = (phase.passed??0) + (phase.failed??0) + (phase.skipped??0);
        const card = document.createElement('article');
        card.className = 'phase-card';
        card.innerHTML = `
          <h4 style="display:flex;justify-content:space-between;align-items:center;">
            <span>${phase.phase_name}</span>
            <span style="font-size:18px;font-weight:800;color:${barColor};">${pct}%</span>
          </h4>
          <div class="progress-wrap" style="margin-bottom:10px;">
            <div class="progress-bar" style="background:${barColor};width:${pct}%;transition:width 0.6s;"></div>
          </div>
          <div class="phase-stat-row"><span class="muted">Passed</span><strong style="color:var(--success);">${phase.passed ?? 0}</strong></div>
          <div class="phase-stat-row"><span class="muted">Failed</span><strong style="color:var(--danger);">${phase.failed ?? 0}</strong></div>
          <div class="phase-stat-row"><span class="muted">Skipped</span><strong style="color:var(--neutral);">${phase.skipped ?? 0}</strong></div>
          <div class="phase-stat-row" style="margin-top:6px;padding-top:6px;border-top:1px solid var(--border);"><span class="muted">Total</span><strong>${total}</strong></div>
        `;
        container.appendChild(card);
      });
    }

    function buildCharts() {
      const statusCtx = document.getElementById('status-chart');
      const phaseCtx = document.getElementById('phase-chart');
      new Chart(statusCtx, {
        type: 'doughnut',
        data: {
          labels: ['Passed', 'Failed', 'Skipped'],
          datasets: [{
            data: [SUMMARY.passed ?? 0, SUMMARY.failed ?? 0, SUMMARY.skipped ?? 0],
            backgroundColor: ['#2fbf71', '#ef4444', '#64748b'],
            borderWidth: 0,
          }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
      });

      const phaseLabels = (PHASE_SUMMARY || []).map((phase) => phase.phase_name);
      const phasePassed = (PHASE_SUMMARY || []).map((phase) => phase.passed ?? 0);
      const phaseFailed = (PHASE_SUMMARY || []).map((phase) => phase.failed ?? 0);
      const phaseSkipped = (PHASE_SUMMARY || []).map((phase) => phase.skipped ?? 0);
      new Chart(phaseCtx, {
        type: 'bar',
        data: {
          labels: phaseLabels,
          datasets: [
            { label: 'Passed', data: phasePassed, backgroundColor: '#2fbf71' },
            { label: 'Failed', data: phaseFailed, backgroundColor: '#ef4444' },
            { label: 'Skipped', data: phaseSkipped, backgroundColor: '#64748b' }
          ]
        },
        options: { responsive: true, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true } } }
      });
    }

    function updateFailedFilterButton() {
      const button = document.getElementById('failed-filter');
      button.classList.toggle('btn-active', state.failedOnly);
      button.textContent = state.failedOnly ? 'Showing Failed Only' : 'Failed Test Quick Filter';
    }

    function resetFilters() {
      state.query = '';
      state.status = 'all';
      state.phase = 'all';
      state.severity = 'all';
      state.sortBy = 'duration';
      state.idFilter = '';
      state.failedOnly = false;
      document.getElementById('filter-id').value = '';
      document.getElementById('filter-status').value = 'all';
      document.getElementById('filter-phase').value = 'all';
      document.getElementById('filter-severity').value = 'all';
      document.getElementById('search-box').value = '';
      document.getElementById('sort-by').value = 'duration';
      updateFailedFilterButton();
      renderTable();
      showToast('Filters reset', 'success');
    }

    function attachEvents() {
      document.getElementById('filter-id').addEventListener('input', (e) => { state.idFilter = e.target.value; renderTable(); });
      document.getElementById('filter-status').addEventListener('change', (e) => { state.status = e.target.value; renderTable(); });
      document.getElementById('filter-phase').addEventListener('change', (e) => { state.phase = e.target.value; renderTable(); });
      document.getElementById('filter-severity').addEventListener('change', (e) => { state.severity = e.target.value; renderTable(); });
      document.getElementById('search-box').addEventListener('input', (e) => { state.query = e.target.value; renderTable(); });
      document.getElementById('sort-by').addEventListener('change', (e) => { state.sortBy = e.target.value; renderTable(); });
      document.getElementById('failed-filter').addEventListener('click', () => {
        state.failedOnly = !state.failedOnly;
        const btn = document.getElementById('failed-filter');
        btn.classList.toggle('btn-active', state.failedOnly);
        btn.textContent = state.failedOnly ? 'Showing Failed Only' : 'Failed Only';
        renderTable();
        showToast(state.failedOnly ? 'Filtered to failed tests' : 'Failed filter cleared', 'success');
      });
      document.getElementById('reset-filters').addEventListener('click', resetFilters);
      document.getElementById('theme-toggle').addEventListener('click', () => {
        document.body.classList.toggle('dark');
        state.darkMode = document.body.classList.contains('dark');
        document.getElementById('theme-toggle').textContent = state.darkMode ? 'Light Mode' : 'Dark Mode';
        showToast(state.darkMode ? 'Dark mode enabled' : 'Light mode enabled', 'success');
      });
      document.getElementById('download-report').addEventListener('click', () => {
        const blob = new Blob([document.documentElement.outerHTML], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'executive_dashboard.html'; a.click();
        URL.revokeObjectURL(url);
        showToast('Report downloaded', 'success');
      });
      document.getElementById('export-csv').addEventListener('click', exportCsv);
      document.getElementById('export-excel').addEventListener('click', exportExcel);
      document.getElementById('copy-errors').addEventListener('click', copyErrors);
    }

    function exportCsv() {
      const rows = getFilteredRows();
      const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
      const header = ['#', 'Test Case ID', 'Description', 'Severity', 'Status', 'Duration (s)', 'Feature', 'Suite', 'Parent Suite', 'Host', 'Framework', 'Error Messages'];
      const csv = [header.join(',')].concat(rows.map((row, i) => {
        const d = row.details || {};
        return [
          esc(i+1), esc(row.tc_id), esc(row.description||''), esc(d.severity||''),
          esc(row.status), esc(row.duration??0), esc(d.feature||''),
          esc(d.suite||''), esc(d.parent_suite||''), esc(d.host||''), esc(d.framework||''),
          esc((d.error_messages||[]).join(' | '))
        ].join(',');
      })).join('\\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'qa_report.csv'; a.click();
      showToast('CSV export prepared — ' + rows.length + ' rows', 'success');
    }

    function exportExcel() {
      const rows = getFilteredRows();
      const headers = '<tr><th>Test Case ID</th><th>Description</th><th>Severity</th><th>Status</th><th>Duration</th><th>Feature</th><th>Suite</th><th>Error Messages</th></tr>';
      const body = rows.map((row) => {
        const d = row.details || {};
        return '<tr><td>' + [
          row.tc_id||'', row.description||'', d.severity||'', row.status||'',
          row.duration||0, d.feature||'', d.suite||'',
          (d.error_messages||[]).join(' | ')
        ].join('</td><td>') + '</td></tr>';
      }).join('');
      const html = '<table>' + headers + body + '</table>';
      const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'qa_report.xls'; a.click();
      showToast('Excel export prepared — ' + rows.length + ' rows', 'success');
    }

    function copyErrors() {
      const rows = getFilteredRows();
      const errors = rows.flatMap((row) => (row.details?.error_messages || []).map((msg) => `[${row.tc_id}] ${msg}`));
      const text = errors.length ? errors.join('\\n') : 'No error messages found in the current filtered result set.';
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => showToast('Error details copied (' + errors.length + ' items)', 'success')).catch(() => showToast('Clipboard unavailable', 'danger'));
      } else {
        window.prompt('Copy error details', text);
        showToast('Please copy the details manually', 'danger');
      }
    }

    function populatePhaseFilter() {
      const select = document.getElementById('filter-phase');
      const phases = Array.from(new Set(TC_DATA.flatMap((row) => Object.keys(row.phase_statuses || {}))));
      phases.forEach((phase) => {
        const option = document.createElement('option');
        option.value = phase;
        option.textContent = phase;
        select.appendChild(option);
      });
    }

    function init() {
      renderSummary();
      renderPhaseSummary();
      renderTopFailures();
      renderSeverityBreakdown();
      buildCharts();
      populatePhaseFilter();
      attachEvents();
      updateFailedFilterButton();
      renderTable();
    }

    init();
  </script>
  <div id="toast" class="toast" aria-live="polite"></div>
</body>
</html>
"""

        return (
            template.replace("__REPORT_TITLE__", payload["report_title"])
            .replace("__APPLICATION_NAME__", payload["application_name"])
            .replace("__SUITE_NAME__", payload["suite_name"])
            .replace("__ENVIRONMENT__", payload["environment"])
            .replace("__EXECUTION_TIME__", payload["execution_time"])
            .replace("__GATE_ICON__", gate_icon)
            .replace("__GATE_LABEL__", gate_label)
            .replace("__GATE_COLOR__", gate_color)
            .replace("__ENV_STRIP__", env_strip_html)
            .replace("__TC_JSON__", tc_json)
            .replace("__SUMMARY_JSON__", summary_json)
            .replace("__PHASE_JSON__", phase_json)
        )

    def get_jinja_render_example(self) -> str:
        """Return a simple Jinja2 example snippet for integration into a Python template pipeline."""
        return """
from jinja2 import Template

template = Template("<h1>{{ report_title }}</h1>")
html = template.render(
    report_title=report_title,
    environment=environment,
    execution_time=execution_time,
    summary=summary,
    tc_data=tc_data,
)
"""

"""
Test Report Analyzer Agent
===========================
Parses pytest HTML reports, identifies failures, and generates detailed analysis.
This agent reviews test execution reports and provides actionable failure insights.
"""

import os
import json
import re
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class TestReportAnalyzerAgent:
    """Agent that analyzes pytest HTML reports for test failures."""

    def __init__(self, report_path: str = None) -> None:
        repo_root = Path(__file__).parent.parent.parent
        if report_path is None:
            default_path = repo_root / "testReport" / "Execution_Backup" / "report" / "pytest_html_report.html"
            report_file  = default_path if default_path.exists() else self._find_report_file(repo_root)
            report_path  = str(report_file) if report_file else str(default_path)
        self.report_path   = report_path
        self.report_exists = os.path.exists(report_path)
        self.soup          = None
        self.report_data   = None
        self.analysis_results = {
            "timestamp":          datetime.now().isoformat(),
            "report_path":        report_path,
            "report_exists":      self.report_exists,
            "summary":            {},
            "failed_tests":       [],
            "passed_tests":       [],
            "skipped_tests":      [],
            "errors":             [],
            "failure_root_causes": [],
            "recommendations":    [],
        }

    @staticmethod
    def _find_report_file(repo_root: Path) -> Optional[Path]:
        candidates = list(repo_root.glob('**/pytest_html_report.html')) + \
                     list(repo_root.glob('**/Test_Report_*.html'))
        if not candidates:
            return None

        def score(path: Path) -> tuple:
            count = 0
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                match   = re.search(r'data-jsonblob="([^"]*)"', content)
                if match:
                    blob  = html.unescape(match.group(1))
                    data  = json.loads(blob)
                    tests = data.get('tests')
                    if isinstance(tests, dict):
                        count = len(tests)
            except Exception:
                count = 0
            return (count, path.stat().st_mtime)

        return max(candidates, key=score)

    def load_report(self) -> bool:
        if not self.report_exists:
            self.analysis_results["errors"].append(f"Report not found at {self.report_path}")
            return False
        if not BS4_AVAILABLE:
            self.analysis_results["errors"].append("beautifulsoup4 not installed — run: pip install beautifulsoup4")
            return False
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            self.soup = BeautifulSoup(html_content, 'html.parser')
            data_container = self.soup.find('div', id='data-container')
            if data_container and data_container.get('data-jsonblob'):
                try:
                    json_str         = html.unescape(data_container.get('data-jsonblob'))
                    self.report_data = json.loads(json_str)
                except Exception as e:
                    self.analysis_results["errors"].append(f"Failed to parse JSON blob: {e}")
            return True
        except Exception as e:
            self.analysis_results["errors"].append(f"Failed to load report: {e}")
            return False

    def extract_summary(self) -> None:
        if self.report_data and 'tests' in self.report_data:
            tests   = self.report_data['tests']
            passed  = sum(1 for tl in tests.values() for t in tl if t.get('result') == 'Passed')
            failed  = sum(1 for tl in tests.values() for t in tl if t.get('result') == 'Failed')
            skipped = sum(1 for tl in tests.values() for t in tl if t.get('result') in ['Skipped', 'Xfailed', 'Xpassed'])
            self.analysis_results["summary"] = {
                "total_tests": passed + failed + skipped,
                "passed":      passed,
                "failed":      failed,
                "skipped":     skipped,
                "pass_rate":   f"{(passed / (passed + failed) * 100) if (passed + failed) > 0 else 0:.2f}%",
            }
            return
        try:
            page_text = self.soup.get_text() if self.soup else ""
            passed    = self._extract_number(page_text, r'(\d+)\s+Passed')
            failed    = self._extract_number(page_text, r'(\d+)\s+Failed')
            skipped   = self._extract_number(page_text, r'(\d+)\s+Skipped|(\d+)\s+Expected failures')
            self.analysis_results["summary"] = {
                "total_tests": passed + failed + skipped,
                "passed":      passed,
                "failed":      failed,
                "skipped":     skipped,
                "pass_rate":   f"{(passed / (passed + failed) * 100) if (passed + failed) > 0 else 0:.2f}%",
            }
        except Exception as e:
            self.analysis_results["errors"].append(f"Failed to extract summary: {e}")

    def extract_test_results(self) -> None:
        if self.report_data and 'tests' in self.report_data:
            for test_name, test_list in self.report_data['tests'].items():
                for test in test_list:
                    info = {
                        'test_name': test_name,
                        'status':    test.get('result', 'unknown').lower(),
                        'duration':  test.get('duration', 'N/A'),
                        'log':       test.get('log', ''),
                    }
                    if info['status'] == 'failed':
                        self.analysis_results["failed_tests"].append(info)
                    elif info['status'] == 'passed':
                        self.analysis_results["passed_tests"].append(info)
                    else:
                        self.analysis_results["skipped_tests"].append(info)
            return
        if not self.soup:
            return
        try:
            for row in self.soup.find_all('tr', class_=re.compile(r'(passed|failed|skipped)')):
                info = self._parse_test_row(row)
                if info:
                    status = info.get("status", "unknown")
                    if status == "failed":
                        self.analysis_results["failed_tests"].append(info)
                    elif status == "passed":
                        self.analysis_results["passed_tests"].append(info)
                    else:
                        self.analysis_results["skipped_tests"].append(info)
        except Exception as e:
            self.analysis_results["errors"].append(f"Failed to extract test results: {e}")

    def analyze_failures(self) -> None:
        for failed_test in self.analysis_results["failed_tests"]:
            log_output = failed_test.get('log', '')
            root_cause = self._determine_root_cause(failed_test['test_name'], log_output)
            self.analysis_results["failure_root_causes"].append({
                "test_name":    failed_test['test_name'],
                "duration":     failed_test['duration'],
                "root_cause":   root_cause,
                "error_snippet": log_output[:300] if log_output else "No log captured",
            })

    def _determine_root_cause(self, test_name: str, log_output: str) -> str:
        if not log_output or log_output == "No log output captured.":
            return "No error details captured"
        patterns = {
            "assertion":        r"AssertionError|assert .* failed|Expected .* but got",
            "timeout":          r"TimeoutError|Timeout|timeout|timed out",
            "connection":       r"ConnectionError|Connection refused|Network error|socket",
            "element_not_found": r"ElementNotFound|NoSuchElement|not found|selector.*invalid",
            "authentication":   r"AuthenticationError|Unauthorized|401|403|login failed",
            "attribute":        r"AttributeError|has no attribute",
            "type":             r"TypeError|type.*incompatible",
            "value":            r"ValueError|invalid value",
        }
        for cause_type, pattern in patterns.items():
            if re.search(pattern, log_output, re.IGNORECASE):
                return f"{cause_type.title()} Error"
        return "Unknown Error - Review logs for details"

    def generate_recommendations(self) -> None:
        summary      = self.analysis_results["summary"]
        failed_count = summary.get("failed", 0)
        total_count  = summary.get("total_tests", 0)
        if total_count == 0:
            self.analysis_results["recommendations"].append(
                "⚠️  No tests found in the report. Check report generation settings."
            )
            return
        if failed_count == 0:
            self.analysis_results["recommendations"].append("✓ All tests passed! No action required.")
        else:
            failure_rate = (failed_count / total_count * 100) if total_count > 0 else 0
            if failure_rate > 50:
                self.analysis_results["recommendations"].append(
                    f"⚠️  High failure rate ({failure_rate:.1f}%). Review test stability and environment setup."
                )
            elif failure_rate > 20:
                self.analysis_results["recommendations"].append(
                    f"⚠️  Moderate failure rate ({failure_rate:.1f}%). Investigate failing test cases."
                )
            for failure in self.analysis_results["failure_root_causes"]:
                root_cause = failure["root_cause"]
                if "Timeout" in root_cause:
                    self.analysis_results["recommendations"].append(
                        f"• {failure['test_name']}: Increase timeout or optimize test execution"
                    )
                elif "Connection" in root_cause:
                    self.analysis_results["recommendations"].append(
                        f"• {failure['test_name']}: Check network connectivity and service availability"
                    )
                elif "Element" in root_cause:
                    self.analysis_results["recommendations"].append(
                        f"• {failure['test_name']}: Verify UI selectors and page structure"
                    )
                elif "Authentication" in root_cause:
                    self.analysis_results["recommendations"].append(
                        f"• {failure['test_name']}: Verify credentials and authentication setup"
                    )

    def _parse_test_row(self, row) -> Optional[Dict]:
        try:
            test_info = {}
            classes   = row.get('class', [])
            if 'passed' in classes:
                test_info['status'] = 'passed'
            elif 'failed' in classes:
                test_info['status'] = 'failed'
            elif 'skipped' in classes:
                test_info['status'] = 'skipped'
            test_col = row.find('td', class_='col-name')
            if test_col:
                test_info['test_name'] = test_col.get_text(strip=True)
            duration_col = row.find('td', class_='col-duration')
            if duration_col:
                test_info['duration'] = duration_col.get_text(strip=True)
            error_div = row.find('div', class_='log')
            if error_div:
                test_info['error_message'] = error_div.get_text(strip=True)[:500]
            return test_info if test_info else None
        except Exception:
            return None

    @staticmethod
    def _extract_number(text: str, pattern: str) -> int:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else 0

    def analyze(self) -> Dict:
        if not self.load_report():
            return self.analysis_results
        self.extract_summary()
        self.extract_test_results()
        if self.analysis_results['summary'].get('total_tests', 0) == 0:
            self.analysis_results['errors'].append(
                'The loaded HTML report contains zero test cases.'
            )
        self.analyze_failures()
        self.generate_recommendations()
        return self.analysis_results

    def generate_detailed_report(self) -> str:
        lines = ["=" * 80, "TEST REPORT ANALYSIS", "=" * 80,
                 f"Generated: {self.analysis_results['timestamp']}",
                 f"Report Path: {self.analysis_results['report_path']}", ""]
        summary = self.analysis_results['summary']
        if summary:
            lines += ["SUMMARY", "-" * 80,
                      f"  Total Tests: {summary.get('total_tests', 0)}",
                      f"  Passed:      {summary.get('passed', 0)}",
                      f"  Failed:      {summary.get('failed', 0)}",
                      f"  Skipped:     {summary.get('skipped', 0)}",
                      f"  Pass Rate:   {summary.get('pass_rate', 'N/A')}", ""]
        if self.analysis_results['failure_root_causes']:
            lines += ["FAILED TESTS & ROOT CAUSE ANALYSIS", "-" * 80]
            for i, failure in enumerate(self.analysis_results['failure_root_causes'], 1):
                lines += [f"\n  {i}. {failure.get('test_name', 'Unknown')}",
                          f"     Root Cause: {failure['root_cause']}",
                          f"     Error: {failure.get('error_snippet', '')[:200]}"]
        if self.analysis_results['recommendations']:
            lines += ["", "RECOMMENDATIONS", "-" * 80]
            for rec in self.analysis_results['recommendations']:
                lines.append(f"  {rec}")
        lines.append("=" * 80)
        return "\n".join(lines)

"""
e2e_testData — Central Path Registry & Test Configuration
===========================================================
Provides:
  - All file/directory paths used across the framework
  - Browser, URL, credentials loaded from Excel with env-var overrides
  - Safe defaults when the Excel file is missing (e.g. fresh clone)

Environment variable overrides (useful in Docker / CI):
  E2E_TEST_DATA_ROOT    — override testData/ directory
  XLSX_API_TESTDATA_FILE — override Excel file path
  E2E_BROWSER           — override browser (chromium | firefox | edge)
  E2E_HEADLESS          — override headless mode (true | false)
  E2E_APP_URL           — override application URL
  E2E_APP_USERNAME      — override login username
  E2E_APP_PASSWORD      — override login password
  LLM_PROVIDER_CONFIG   — override LLM config file path
  STORAGE_STATE_FOLDER  — override storageState directory
"""

import os
import sys
import inspect

import openpyxl

# ── Path setup ────────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir  = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

repo_root  = parent_dir
data_root  = os.environ.get("E2E_TEST_DATA_ROOT", os.path.join(repo_root, "testData"))
folderPath = os.path.join(data_root, "")

# ── File / directory paths ────────────────────────────────────────────────────
xlsx_apiTestData_file      = os.environ.get(
    "XLSX_API_TESTDATA_FILE",
    os.path.join(folderPath, "API_testData.xlsx"),
)
testReport_exeBackupPath   = os.environ.get(
    "TEST_REPORT_EXECUTION_BACKUP",
    os.path.join(repo_root, "testReport", "Execution_Backup"),
) + os.sep
testReport_APIresponsesPath = os.path.join(testReport_exeBackupPath, "API_responses") + os.sep
screenshots_folderPath      = os.environ.get(
    "TEST_REPORT_UI_SCREENSHOTS",
    os.path.join(repo_root, "testReport", "UI_Screenshots"),
) + os.sep
backup_dir   = os.path.join(testReport_exeBackupPath, "backup")
report_dir   = os.path.join(testReport_exeBackupPath, "report")
report_file  = os.path.join(report_dir, "pytest_html_report.html")

llm_provider_config = os.environ.get(
    "LLM_PROVIDER_CONFIG",
    os.path.join(repo_root, "config", "config.json"),
)
testReport_UIScreenshotsPath = os.environ.get(
    "TEST_REPORT_UI_SCREENSHOTS",
    os.path.join(repo_root, "testReport", "UI_Screenshots"),
)
testReport_UIVideosPath = os.environ.get(
    "TEST_REPORT_UI_VIDEOS",
    os.path.join(repo_root, "testReport", "Videos"),
)
testReport_UITracesPath = os.environ.get(
    "TEST_REPORT_UI_TRACES",
    os.path.join(repo_root, "testReport", "Traces"),
)
storage_state_folder = os.environ.get(
    "STORAGE_STATE_FOLDER",
    os.path.join(repo_root, "storageState"),
)
storage_state_path = os.path.join(storage_state_folder, "storageState.json")

# ── Ensure required directories exist ────────────────────────────────────────
for _path in [
    data_root,
    os.path.dirname(xlsx_apiTestData_file),
    testReport_exeBackupPath,
    testReport_APIresponsesPath,
    screenshots_folderPath,
    testReport_UIScreenshotsPath,
    testReport_UIVideosPath,
    testReport_UITracesPath,
    storage_state_folder,
]:
    os.makedirs(_path, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Excel helpers — safe reads with fallback defaults
# ─────────────────────────────────────────────────────────────────────────────

def testData(sheetname: str, rowNo: int, colNo: int):
    """
    Read a single cell value from the Excel test data file.

    Returns None if the file is missing or the cell is empty.
    Does NOT raise — callers should provide a default.
    """
    import glob
    files = glob.glob(xlsx_apiTestData_file)
    if not files:
        return None
    try:
        max_file = max(files, key=os.path.getctime)
        wb       = openpyxl.load_workbook(max_file)
        ws       = wb[sheetname]
        return ws.cell(row=rowNo, column=colNo).value
    except Exception:
        return None


def _safe_str(value, default: str = "") -> str:
    """Return str(value).strip() or default if value is None/empty."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def save_api_resp_into_file(filename: str, response: str) -> None:
    """Write an API response to a JSON file in the API responses directory."""
    filepath = os.path.join(testReport_APIresponsesPath, f"{filename}_resp.json")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(response)


# ─────────────────────────────────────────────────────────────────────────────
# Browser & application configuration
# Env vars take priority; Excel values are used as fallback;
# hardcoded defaults are used when both are unavailable (fresh clone).
# ─────────────────────────────────────────────────────────────────────────────

# Browser name: chromium | firefox | edge
browser_name: str = _safe_str(
    os.environ.get("E2E_BROWSER") or testData("API_Common_Data", 3, 2),
    default="chromium",
).lower()

# Headless mode
_headless_raw = os.environ.get("E2E_HEADLESS") or testData("API_Common_Data", 4, 2)
headlessMode: bool = str(_headless_raw).strip().lower() in ("true", "1", "yes", "y") \
    if _headless_raw is not None else False

# Application URL
url: str = _safe_str(
    os.environ.get("E2E_APP_URL") or testData("API_Common_Data", 5, 2),
    default="http://localhost",
)

# Login credentials
username: str = _safe_str(
    os.environ.get("E2E_APP_USERNAME") or testData("API_Common_Data", 6, 2),
    default="Admin",
)
password: str = _safe_str(
    os.environ.get("E2E_APP_PASSWORD") or testData("API_Common_Data", 7, 2),
    default="admin123",
)

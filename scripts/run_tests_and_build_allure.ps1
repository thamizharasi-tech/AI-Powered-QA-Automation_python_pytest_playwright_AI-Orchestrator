# Run tests and build Allure report
# Usage:
# powershell -ExecutionPolicy Bypass -File .\scripts\run_tests_and_build_allure.ps1

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------
# Java & Allure Configuration
# ------------------------------------------------------------------
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot"
$env:PATH = "C:\allure-2.44.0\allure-2.44.0\bin;$env:JAVA_HOME\bin;$env:PATH"

# ------------------------------------------------------------------
# Report Paths
# ------------------------------------------------------------------
$baseReportDir = "testReport\Execution_Backup\report"
$resultsDir    = "$baseReportDir\allure-results"
$reportDir     = "$baseReportDir\allure-report"

# Timestamped backup folder
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "$baseReportDir\History\allure-report_$timestamp"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      QA Automation Execution"
Write-Host "=========================================" -ForegroundColor Cyan

# ------------------------------------------------------------------
# Validate Java
# ------------------------------------------------------------------
Write-Host "`nChecking Java..." -ForegroundColor Yellow
java -version

# ------------------------------------------------------------------
# Validate Allure
# ------------------------------------------------------------------
Write-Host "`nChecking Allure..." -ForegroundColor Yellow
allure --version

# ------------------------------------------------------------------
# Clean Previous Results
# ------------------------------------------------------------------
Write-Host "`nCleaning previous Allure results..." -ForegroundColor Yellow

Remove-Item $resultsDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null

# ------------------------------------------------------------------
# Execute Tests
# ------------------------------------------------------------------
Write-Host "`nRunning Pytest..." -ForegroundColor Yellow
pytest --clean-alluredir --alluredir=$resultsDir

# ------------------------------------------------------------------
# Archive previous generated report if present
# ------------------------------------------------------------------
Write-Host "`nArchiving previous Allure report (if present)..." -ForegroundColor Yellow
if (Test-Path $reportDir) {
    New-Item -ItemType Directory -Path (Split-Path $archiveDir) -Force | Out-Null
    Move-Item -Path $reportDir -Destination $archiveDir -Force
    Write-Host "Archived existing report to: $archiveDir" -ForegroundColor Green
}

# ------------------------------------------------------------------
# Generate the Allure HTML report
# ------------------------------------------------------------------
Write-Host "`nGenerating Allure report..." -ForegroundColor Yellow
allure generate $resultsDir -o $reportDir --clean
Write-Host "`nAllure report generated: $reportDir" -ForegroundColor Green

# ------------------------------------------------------------------
# Generate AI dashboard from Allure results
# ------------------------------------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$generatorScript = Join-Path $scriptDir "generate_ai_dashboard.py"
$venvPython = Join-Path $scriptDir "..\venv\Scripts\python.exe"

Write-Host "`nGenerating AI dashboard from Allure results..." -ForegroundColor Yellow
if (Test-Path $venvPython) {
    & $venvPython $generatorScript --allure-results-dir "$resultsDir"
} else {
    python $generatorScript --allure-results-dir "$resultsDir"
}

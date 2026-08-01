// ─────────────────────────────────────────────────────────────────────────────
// QA AI Automation Framework v5.1 — Jenkins Pipeline
// ─────────────────────────────────────────────────────────────────────────────
// Stages:
//   1. Checkout
//   2. Install Dependencies
//   3. Install Playwright Browsers
//   4. Install Allure CLI
//   5. Prepare Directories
//   6. Run API Tests        (fast, no browser, ~15s)
//   7. Run UI Smoke Tests   (headless, ~5 min)
//   8. Run UI Regression    (headless, full suite, ~20 min)
//   9. Generate Allure Report
//  10. Generate AI Dashboard
//
// Test Suites:
//   API:        tests/api/test_positive_user_creation.py  (5 tests)
//   UI Smoke:   pytest -m smoke                           (fast gate)
//   UI Full:    tests/ui/                                 (66 tests)
//     ├── test_login.py                (4)
//     ├── test_feature_login.py        (3)
//     ├── test_add_employee.py         (14)
//     ├── test_employee_search.py      (10)
//     ├── test_edit_employee.py        (4)   ← NEW v5.1
//     ├── test_delete_employee.py      (3)   ← NEW v5.1
//     ├── test_user_management.py      (2)
//     ├── test_admin_user_management.py(4)   ← NEW v5.1
//     ├── test_leave_management.py     (3)
//     ├── test_apply_for_leave.py      (18)
//     └── test_happy_path_e2e.py       (1)
//
// Reports (auto-generated after every run):
//   - Allure HTML Report
//   - AI Dashboard (executive summary + quality gate)
//   - pytest HTML Report
// ─────────────────────────────────────────────────────────────────────────────

pipeline {
  agent {
    docker {
      image 'mcr.microsoft.com/playwright/python:v1.49.0-jammy'
      // -u root required for apt-get in Install Allure CLI stage
      args '-u root'
    }
  }

  environment {
    ALLURE_VERSION  = '2.44.0'
    RESULTS_DIR     = 'testReport/Execution_Backup/report/allure-results'
    REPORT_DIR      = 'testReport/Execution_Backup/report/allure-report'
    DASHBOARD_PATH  = 'testReport/Execution_Backup/report/ai_dashboard_report.html'
    HTML_REPORT     = 'testReport/Execution_Backup/report/pytest_html_report.html'
    // Always headless in CI — overrides Excel config
    E2E_HEADLESS    = 'true'
    E2E_BROWSER     = 'chromium'
  }

  stages {

    // ── Stage 1: Checkout ────────────────────────────────────────────────────
    stage('Checkout') {
      steps {
        checkout scm
        echo "✅ Checked out: ${env.GIT_BRANCH} @ ${env.GIT_COMMIT?.take(8)}"
      }
    }

    // ── Stage 2: Install Python Dependencies ─────────────────────────────────
    stage('Install Dependencies') {
      steps {
        sh '''
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          echo "✅ Python dependencies installed"
          pip list | grep -E "pytest|playwright|allure|openpyxl|requests|ollama"
        '''
      }
    }

    // ── Stage 3: Install Playwright Browsers ─────────────────────────────────
    stage('Install Playwright Browsers') {
      steps {
        sh '''
          python -m playwright install --with-deps chromium
          echo "✅ Playwright Chromium installed"
        '''
      }
    }

    // ── Stage 4: Install Allure CLI ───────────────────────────────────────────
    // Must be installed BEFORE tests run — conftest.py calls allure generate
    // inside pytest_sessionfinish(), so CLI must be available during execution.
    stage('Install Allure CLI') {
      steps {
        sh '''
          apt-get update -qq && apt-get install -y --no-install-recommends \
            curl unzip openjdk-17-jre-headless
          curl -fsSL -o /tmp/allure.zip \
            https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip
          unzip -q /tmp/allure.zip -d /opt
          ln -sf /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure
          rm -f /tmp/allure.zip
          allure --version
          echo "✅ Allure CLI ${ALLURE_VERSION} installed"
        '''
      }
    }

    // ── Stage 5: Prepare Directories ─────────────────────────────────────────
    stage('Prepare Directories') {
      steps {
        sh '''
          mkdir -p ${RESULTS_DIR} \
                   testReport/Execution_Backup/report \
                   testReport/Execution_Backup/archive \
                   testReport/Execution_Backup/backup \
                   testReport/UI_Screenshots \
                   testReport/Videos \
                   testReport/Traces \
                   testData \
                   storageState \
                   ai_orchestrator/pipeline_state
          echo "✅ Directories prepared"
        '''
      }
    }

    // ── Stage 6: Run API Tests ────────────────────────────────────────────────
    // Fast gate — no browser required, ~15 seconds
    // Tests: POST/GET/PUT/DELETE /user against Petstore API
    stage('Run API Tests') {
      steps {
        sh '''
          echo "🔵 Running API tests (5 tests, ~15s)..."
          pytest tests/api/ -m api -v --tb=short \
            --alluredir=${RESULTS_DIR} \
            --html=${HTML_REPORT} --self-contained-html \
            2>&1 | tee api_test_output.txt
          echo "✅ API tests complete"
        '''
      }
      post {
        always {
          echo "API test output saved to api_test_output.txt"
        }
      }
    }

    // ── Stage 7: Run UI Smoke Tests ───────────────────────────────────────────
    // Fast CI gate — only smoke-marked tests
    stage('Run UI Smoke Tests') {
      steps {
        sh '''
          echo "🔵 Running UI smoke tests..."
          pytest -m smoke -v --tb=short \
            --alluredir=${RESULTS_DIR} \
            --html=${HTML_REPORT} --self-contained-html \
            2>&1 | tee smoke_test_output.txt
          echo "✅ Smoke tests complete"
        '''
      }
    }

    // ── Stage 8: Run Full UI Regression ──────────────────────────────────────
    // Full UI test suite — 66 tests across all modules
    // Modules: Login, Add Employee, Employee Search, Edit Employee (NEW),
    //          Delete Employee (NEW), User Management, Admin User Management (NEW),
    //          Leave Management, Apply for Leave, Happy Path E2E
    stage('Run UI Regression') {
      steps {
        sh '''
          echo "🔵 Running full UI regression (66 tests)..."
          pytest tests/ui/ -m ui -v --tb=short \
            --alluredir=${RESULTS_DIR} \
            --html=${HTML_REPORT} --self-contained-html \
            2>&1 | tee ui_test_output.txt
          echo "✅ UI regression complete"
        '''
      }
    }

    // ── Stage 9: Generate Allure Report ──────────────────────────────────────
    stage('Generate Allure Report') {
      steps {
        sh '''
          allure generate ${RESULTS_DIR} -o ${REPORT_DIR} --clean
          echo "✅ Allure report generated: ${REPORT_DIR}/index.html"
        '''
      }
    }

    // ── Stage 10: Generate AI Dashboard ──────────────────────────────────────
    stage('Generate AI Dashboard') {
      steps {
        sh '''
          python scripts/generate_ai_dashboard.py
          echo "✅ AI Dashboard generated: ${DASHBOARD_PATH}"
        '''
      }
    }

  }

  // ── Post Actions ─────────────────────────────────────────────────────────────
  post {
    always {
      // Archive all test reports (Allure HTML, AI Dashboard, pytest-html, logs)
      archiveArtifacts(
        artifacts: 'testReport/Execution_Backup/report/**,*_test_output.txt',
        fingerprint: true,
        allowEmptyArchive: true
      )

      // Publish Allure report in Jenkins UI (requires Allure Jenkins Plugin)
      allure([
        includeProperties: true,
        jdk: '',
        results: [[path: "${env.RESULTS_DIR}"]]
      ])

      // Clean up test output files
      sh 'rm -f api_test_output.txt smoke_test_output.txt ui_test_output.txt || true'
    }

    success {
      echo "✅ Pipeline PASSED — All tests passed and reports generated."
      echo "📊 Allure Report: ${env.BUILD_URL}allure"
      echo "📈 AI Dashboard: ${env.BUILD_URL}artifact/testReport/Execution_Backup/report/ai_dashboard_report.html"
      // Uncomment to enable Slack notification:
      // slackSend(color: 'good', message: "✅ QA Pipeline PASSED: ${env.JOB_NAME} #${env.BUILD_NUMBER} | ${env.BUILD_URL}")
    }

    failure {
      echo "❌ Pipeline FAILED — Check test results and Allure report."
      echo "📊 Allure Report: ${env.BUILD_URL}allure"
      // Uncomment to enable Slack notification:
      // slackSend(color: 'danger', message: "❌ QA Pipeline FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER} | ${env.BUILD_URL}")
    }

    unstable {
      echo "⚠️ Pipeline UNSTABLE — Some tests failed. Check Allure report for details."
      // Uncomment to enable Slack notification:
      // slackSend(color: 'warning', message: "⚠️ QA Pipeline UNSTABLE: ${env.JOB_NAME} #${env.BUILD_NUMBER} | ${env.BUILD_URL}")
    }
  }
}

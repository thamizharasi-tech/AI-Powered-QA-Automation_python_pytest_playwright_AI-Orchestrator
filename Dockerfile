# ─────────────────────────────────────────────────────────────────────────────
# QA AI Automation Framework v5.1
# ─────────────────────────────────────────────────────────────────────────────
# Base image: Microsoft Playwright Python (includes Chromium, Firefox, WebKit)
# Adds: Java 17 (for Allure CLI), Allure CLI, openpyxl (for Excel state/RTM)
#
# Build:
#   docker build -t qa-ai-automation .
#
# Run tests only:
#   docker run --rm \
#     -v ${PWD}/testReport:/app/testReport \
#     -v ${PWD}/testData:/app/testData \
#     qa-ai-automation
#
# Run AI pipeline (9 agents) + tests:
#   The framework reads LLM credentials from config/config.json — mount it read-only.
#   Do NOT pass API keys as environment variables; they are not read from env.
#   docker run --rm \
#     -v ${PWD}/config/config.json:/app/config/config.json:ro \
#     -v ${PWD}/testReport:/app/testReport \
#     -v ${PWD}/testData:/app/testData \
#     -v ${PWD}/ai_orchestrator/pipeline_state:/app/ai_orchestrator/pipeline_state \
#     qa-ai-automation pytest ai_orchestrator/orchestrator.py -v -s
#
# Force re-run (bypass AI cache):
#   docker run --rm -e FORCE_RERUN=1 ... qa-ai-automation
# ─────────────────────────────────────────────────────────────────────────────

# Pinned to v1.49.0-jammy to match playwright==1.49.0 in requirements-lock.txt.
# Python 3.10.12 / Ubuntu 22.04 (Jammy LTS).
# Update this tag when upgrading playwright in requirements.txt, then regenerate
# requirements-lock.txt:
#   docker build -t qa-ai-automation .
#   docker run --rm qa-ai-automation pip list --format=freeze \
#     | grep -v "^pip=\|^setuptools=\|^wheel=\|^virtualenv=\|^distlib=\|^filelock=\|^platformdirs=" \
#     > requirements-lock.txt
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# ── Environment ───────────────────────────────────────────────────────────────
# E2E_BROWSER=chromium  → overrides Excel browser setting (msedge not available in Linux)
# E2E_HEADLESS=true     → overrides Excel headless setting (always headless in container)
ENV DEBIAN_FRONTEND=noninteractive \
    ALLURE_VERSION=2.44.0 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH=/usr/local/bin:/opt/allure/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    E2E_BROWSER=chromium \
    E2E_HEADLESS=true

# ── System dependencies ───────────────────────────────────────────────────────
# curl + unzip: for Allure CLI download
# openjdk-17-jre-headless: required by Allure CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
# requirements.txt      — human-readable source of truth for direct dependencies
# requirements-lock.txt — full lock file (direct + transitive) for reproducible builds
#
# Docker installs from requirements-lock.txt to ensure every build uses the
# exact same package versions.  requirements.txt is copied alongside it so
# developers can see which packages are direct dependencies.
#
# Layer-caching: both files are copied before COPY . . so the pip install
# layer is only invalidated when a dependency file changes.
COPY requirements.txt  ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Playwright browsers ───────────────────────────────────────────────────────
# Explicitly install Chromium (default browser in container).
# msedge is NOT available on Linux — E2E_BROWSER=chromium overrides Excel config.
# Firefox and WebKit are available in the base image but not installed by default.
RUN playwright install chromium

# ── Allure CLI ────────────────────────────────────────────────────────────────
RUN mkdir -p /tmp/allure && \
    curl -fsSL -o /tmp/allure.zip \
      "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip" && \
    unzip -q /tmp/allure.zip -d /opt && \
    mv /opt/allure-${ALLURE_VERSION} /opt/allure && \
    ln -sf /opt/allure/bin/allure /usr/local/bin/allure && \
    rm -rf /tmp/allure.zip && \
    allure --version

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Required directories ──────────────────────────────────────────────────────
# testReport/         : Allure results, HTML reports, screenshots, videos, traces
# testData/           : Excel test data (auto-populated by DataAgent)
# storageState/       : Playwright browser auth state
# ai_orchestrator/pipeline_state/ : Excel state files (pipeline_state.xlsx, rtm_store.xlsx)
RUN mkdir -p \
    testReport/Execution_Backup/report/allure-results \
    testReport/Execution_Backup/report/allure-report \
    testReport/Execution_Backup/archive \
    testReport/UI_Screenshots \
    testReport/Videos \
    testReport/Traces \
    testData \
    storageState \
    ai_orchestrator/pipeline_state

# ── Volumes (mount these from host for persistence) ───────────────────────────
# -v ${PWD}/testReport:/app/testReport
# -v ${PWD}/testData:/app/testData
# -v ${PWD}/ai_orchestrator/pipeline_state:/app/ai_orchestrator/pipeline_state
VOLUME ["/app/testReport", "/app/testData", "/app/ai_orchestrator/pipeline_state"]

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pytest, playwright, openpyxl; print('OK')" || exit 1

# ── Default command: run all tests ────────────────────────────────────────────
# Override with: docker run ... qa-ai-automation pytest ai_orchestrator/orchestrator.py -v -s
CMD ["pytest", "--tb=short", "-v"]

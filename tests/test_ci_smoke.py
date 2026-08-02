"""
test_ci_smoke.py — CI Gate Smoke Tests
======================================
Fast, dependency-free sanity checks that must pass on every push/PR.

These tests must NOT require:
  - a browser session
  - a live API / application under test
  - an LLM provider or config/config.json (which holds secrets)

Run locally:
    pytest -m smoke -q
"""

import importlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.smoke
def test_core_dependencies_importable():
    """All third-party packages required at import time are installed."""
    for module in ("pytest", "playwright", "openpyxl", "requests", "allure"):
        assert importlib.import_module(module) is not None


@pytest.mark.smoke
def test_project_structure_present():
    """Key framework directories exist in the checkout."""
    for folder in ("core", "tests", "ai_orchestrator", "config"):
        assert (PROJECT_ROOT / folder).is_dir(), f"Missing directory: {folder}"


@pytest.mark.smoke
def test_framework_modules_import():
    """Core framework modules import cleanly (no syntax/import errors)."""
    for module in (
        "core.e2e_testData",
        "core.logger.logger",
        "core.config.allure_config",
        "ai_orchestrator.llm_factory",
    ):
        assert importlib.import_module(module) is not None


@pytest.mark.smoke
def test_llm_provider_registry_not_empty():
    """At least one LLM provider is registered (no config.json needed)."""
    from ai_orchestrator.llm_factory import list_registered_providers

    assert list_registered_providers(), "No LLM providers registered"


@pytest.mark.smoke
def test_report_directories_creatable(tmp_path):
    """Report directory creation logic works on the CI filesystem."""
    target = tmp_path / "testReport" / "Execution_Backup" / "report"
    target.mkdir(parents=True, exist_ok=True)
    assert target.is_dir()

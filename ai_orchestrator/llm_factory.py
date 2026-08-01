"""
LLM Factory — Extensible Plugin Registry
==========================================
Reads config/config.json and returns the appropriate LLM provider instance.

DEFAULT PROVIDER
================
  Ollama — local LLM server (llama3, mistral, qwen, etc.)
  Install: https://ollama.ai
  Run:     ollama pull llama3
  Start:   ollama serve

ADDING A NEW LLM PROVIDER
==========================
To add support for a new LLM (e.g. OpenAI, Gemini, Anthropic, etc.):

  Step 1 — Create the provider file:
    ai_orchestrator/providers/my_provider.py

    from ai_orchestrator.providers.base_provider import BaseLLMProvider

    class MyProvider(BaseLLMProvider):
        def __init__(self, config: dict) -> None:
            # read from config["my_provider"]
            ...
        def generate(self, prompt: str) -> str:
            # call your LLM API
            return response_text

  Step 2 — Register it in the PROVIDER_REGISTRY below:
    PROVIDER_REGISTRY["my_provider"] = _load_my_provider

  Step 3 — Add config template to config/config.example.json:
    "my_provider": {
      "api_key": "...",
      "model":   "..."
    }

  Step 4 — Set "provider": "my_provider" in config/config.json

No other files need to change. The gateway, workflow, and all agents
are provider-agnostic — they only call provider.generate(prompt).

PROVIDER REGISTRY
=================
Each entry is a lazy loader function that imports the provider class
only when it is actually needed. This keeps startup fast and avoids
ImportError for providers whose SDK is not installed.
"""

import json
import logging
from pathlib import Path
from typing import Callable, Dict

from core.e2e_testData import llm_provider_config
from ai_orchestrator.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lazy loader functions — one per provider
# Each function receives the full config dict and returns a BaseLLMProvider.
# ─────────────────────────────────────────────────────────────────────────────

def _load_ollama(config: dict) -> BaseLLMProvider:
    """Ollama — local models (llama3, mistral, qwen, etc.)."""
    from ai_orchestrator.providers.ollama_provider import OllamaProvider
    return OllamaProvider(config)


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER REGISTRY
# Add new providers here — no other files need to change.
# ─────────────────────────────────────────────────────────────────────────────

PROVIDER_REGISTRY: Dict[str, Callable[[dict], BaseLLMProvider]] = {
    "ollama": _load_ollama,
    # ── Add future providers below ──────────────────────────────────────────
    # "openai":    _load_openai,
    # "azure":     _load_azure,
    # "gemini":    _load_gemini,
    # "anthropic": _load_anthropic,
    # "cohere":    _load_cohere,
    # "mistral":   _load_mistral,
    # "my_custom": _load_my_custom,
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_llm() -> BaseLLMProvider:
    """
    Read config/config.json and return the configured LLM provider.

    The provider is looked up in PROVIDER_REGISTRY by the "provider" key
    in config.json. If the provider is not registered, a clear error is
    raised with instructions on how to add it.

    Returns
    -------
    BaseLLMProvider
        An instantiated provider ready to call .generate(prompt).

    Raises
    ------
    FileNotFoundError
        If config/config.json does not exist.
    ValueError
        If the provider name is not in PROVIDER_REGISTRY.
    """
    config_path = Path(llm_provider_config)
    if not config_path.exists():
        raise FileNotFoundError(
            f"LLM config not found: {config_path}\n"
            "Copy config/config.example.json to config/config.json "
            "and set your provider settings."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    provider_name = config.get("provider", "ollama").strip().lower()
    logger.info("[LLMFactory] Provider: %s", provider_name)
    print(f"[LLMFactory] Using provider: {provider_name}")

    loader = PROVIDER_REGISTRY.get(provider_name)
    if loader is None:
        registered = ", ".join(sorted(PROVIDER_REGISTRY.keys()))
        raise ValueError(
            f"Unknown LLM provider: '{provider_name}'.\n"
            f"Registered providers: {registered}\n\n"
            "To add a new provider:\n"
            "  1. Create ai_orchestrator/providers/<name>_provider.py\n"
            "     implementing BaseLLMProvider.generate(prompt) -> str\n"
            "  2. Add a loader function and register it in\n"
            "     ai_orchestrator/llm_factory.py PROVIDER_REGISTRY\n"
            "  3. Add config template to config/config.example.json\n"
            "  4. Set \"provider\": \"<name>\" in config/config.json"
        )

    return loader(config)


def list_registered_providers() -> list:
    """Return the names of all currently registered LLM providers."""
    return sorted(PROVIDER_REGISTRY.keys())


def register_provider(name: str, loader: Callable[[dict], BaseLLMProvider]) -> None:
    """
    Dynamically register a new LLM provider at runtime.

    Parameters
    ----------
    name   : str — provider name (used as "provider" value in config.json)
    loader : callable — function(config: dict) -> BaseLLMProvider

    Example
    -------
    from ai_orchestrator.llm_factory import register_provider

    def _load_my_llm(config):
        from my_package import MyLLM
        return MyLLM(config["my_llm"]["api_key"])

    register_provider("my_llm", _load_my_llm)
    """
    PROVIDER_REGISTRY[name] = loader
    logger.info("[LLMFactory] Registered provider: %s", name)

"""
base_provider.py — Abstract Base Class for LLM Providers
==========================================================
Defines the contract that every LLM provider must implement.

All providers (Ollama, OpenAI, Gemini, etc.) must extend
BaseLLMProvider and implement the generate() method.
"""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider implementations.

    Every provider must implement generate(prompt) which sends a prompt
    to the underlying LLM and returns the text response as a string.

    Concrete implementations:
      - OllamaProvider  (ai_orchestrator/providers/ollama_provider.py)

    To add a new provider:
      1. Create ai_orchestrator/providers/<name>_provider.py
      2. Extend BaseLLMProvider and implement generate()
      3. Register in ai_orchestrator/llm_factory.py PROVIDER_REGISTRY
      4. Add config block to config/config.example.json
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return the text response.

        Parameters
        ----------
        prompt : str — the full prompt to send to the LLM

        Returns
        -------
        str — the LLM's text response

        Raises
        ------
        Exception — any provider-specific error (network, auth, quota, etc.)
        """
        ...

"""
Ollama LLM Provider (local models: llama3, mistral, qwen, etc.)

Configuration (config/config.json):
    {
      "provider": "ollama",
      "ollama": {
        "model": "llama3"
      }
    }

Requirements:
    pip install ollama
    ollama pull llama3   (or any other model)
    ollama serve         (start the local server)
"""

from ai_orchestrator.providers.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """LLM provider for Ollama (local models)."""

    def __init__(self, config: dict) -> None:
        self.model: str = config.get("ollama", {}).get("model", "llama3")

    def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the text response."""
        try:
            from ollama import chat
        except ImportError as exc:
            raise ImportError(
                "ollama package is required for OllamaProvider.\n"
                "Install it with: pip install ollama\n"
                "Then start the server: ollama serve"
            ) from exc

        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.message
        if message is None:
            raise RuntimeError(
                f"OllamaProvider: response contained no message. Model: {self.model!r}"
            )
        content = message.content
        if content is None:
            raise RuntimeError(
                f"OllamaProvider: response message had no content. Model: {self.model!r}"
            )
        return content

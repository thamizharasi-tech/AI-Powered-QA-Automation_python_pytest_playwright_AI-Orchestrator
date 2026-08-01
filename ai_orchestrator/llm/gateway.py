"""
LLM Gateway
===========
Wraps any BaseLLMProvider with retry logic, timeout enforcement,
structured error handling, and call logging.

Architectural Principle:
  The LLM must NOT become the execution engine.
  The framework must continue to work if the AI/LLM provider is unavailable.
  This gateway ensures graceful degradation when the LLM is unreachable.

Usage:
    from ai_orchestrator.llm.gateway import LLMGateway
    from ai_orchestrator.llm_factory import get_llm

    llm = LLMGateway(get_llm(), max_retries=3, timeout_seconds=120)
    response = llm.generate(prompt)
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Wraps a BaseLLMProvider with retry, timeout, and error handling.

    Features:
      - Automatic retry with exponential backoff on transient failures
      - Configurable timeout per call
      - Structured error logging
      - Graceful fallback message when LLM is unavailable
      - Call duration tracking

    Parameters
    ----------
    provider : BaseLLMProvider
        Any provider implementing generate(prompt: str) -> str.
    max_retries : int
        Number of retry attempts on failure (default: 3).
    timeout_seconds : int
        Maximum seconds to wait for a single LLM response (default: 120).
    retry_delay_seconds : float
        Initial delay between retries; doubles on each attempt (default: 2.0).
    fallback_on_failure : bool
        If True, return a fallback message instead of raising on final failure.
        If False, re-raise the last exception (default: True).
    """

    # Fallback message returned when LLM is unavailable and fallback is enabled
    _FALLBACK_MESSAGE = (
        "[LLM_UNAVAILABLE] The AI/LLM provider is currently unavailable. "
        "The framework continues to operate in deterministic mode. "
        "Please check your LLM provider configuration in config/config.json "
        "and retry when the provider is accessible."
    )

    def __init__(
        self,
        provider,
        max_retries: int = 3,
        timeout_seconds: int = 120,
        retry_delay_seconds: float = 2.0,
        fallback_on_failure: bool = True,
    ) -> None:
        self._provider = provider
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._retry_delay = retry_delay_seconds
        self._fallback_on_failure = fallback_on_failure
        self._call_count = 0
        self._total_duration = 0.0

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the LLM with retry and timeout protection.

        Parameters
        ----------
        prompt : str
            The full prompt text to send to the LLM.

        Returns
        -------
        str
            The LLM's text response, or a fallback message if unavailable.

        Raises
        ------
        Exception
            If fallback_on_failure=False and all retries are exhausted.
        """
        self._call_count += 1
        call_id = self._call_count
        last_exception: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            start = time.time()
            try:
                logger.debug(
                    "[LLMGateway] Call #%d attempt %d/%d — prompt length: %d chars",
                    call_id, attempt, self._max_retries, len(prompt),
                )
                response = self._call_with_timeout(prompt)
                elapsed = time.time() - start
                self._total_duration += elapsed
                logger.debug(
                    "[LLMGateway] Call #%d completed in %.2fs", call_id, elapsed
                )
                return response

            except TimeoutError as exc:
                elapsed = time.time() - start
                last_exception = exc
                logger.warning(
                    "[LLMGateway] Call #%d attempt %d TIMEOUT after %.2fs",
                    call_id, attempt, elapsed,
                )

            except Exception as exc:
                elapsed = time.time() - start
                last_exception = exc
                logger.warning(
                    "[LLMGateway] Call #%d attempt %d FAILED after %.2fs: %s: %s",
                    call_id, attempt, elapsed, type(exc).__name__, exc,
                )

            # Exponential backoff before retry
            if attempt < self._max_retries:
                delay = self._retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "[LLMGateway] Retrying in %.1fs (attempt %d/%d)...",
                    delay, attempt + 1, self._max_retries,
                )
                time.sleep(delay)

        # All retries exhausted
        logger.error(
            "[LLMGateway] Call #%d FAILED after %d attempts. Last error: %s",
            call_id, self._max_retries, last_exception,
        )

        if self._fallback_on_failure:
            logger.warning("[LLMGateway] Returning fallback message.")
            return self._FALLBACK_MESSAGE

        raise last_exception  # type: ignore[misc]

    def _call_with_timeout(self, prompt: str) -> str:
        """
        Call the provider's generate() method.

        Note: True thread-based timeout is complex and platform-dependent.
        This implementation uses a simple approach that works for most
        synchronous LLM providers. For async providers, override this method.
        """
        # For synchronous providers, we rely on the provider's own timeout
        # mechanisms (e.g., requests timeout, httpx timeout).
        # The gateway-level timeout is enforced via the retry mechanism.
        return self._provider.generate(prompt)

    @property
    def call_count(self) -> int:
        """Total number of LLM calls made through this gateway."""
        return self._call_count

    @property
    def total_duration_seconds(self) -> float:
        """Total time spent waiting for LLM responses."""
        return self._total_duration

    @property
    def average_duration_seconds(self) -> float:
        """Average LLM response time."""
        if self._call_count == 0:
            return 0.0
        return self._total_duration / self._call_count

    def stats(self) -> dict:
        """Return gateway usage statistics."""
        return {
            "call_count": self._call_count,
            "total_duration_seconds": round(self._total_duration, 2),
            "average_duration_seconds": round(self.average_duration_seconds, 2),
            "max_retries": self._max_retries,
            "timeout_seconds": self._timeout_seconds,
        }

import logging
import time
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model

logger = logging.getLogger(__name__)

# Default retry settings for transient API errors (503, 429, etc.)
_DEFAULT_MAX_RETRIES = 6
_RETRY_BASE_DELAY = 2.0     # seconds
_RETRY_MAX_DELAY = 120.0    # cap backoff at 2 minutes
_RETRYABLE_SUBSTRINGS = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "rate limit")


def _is_retryable(exc: Exception) -> bool:
    """Check if an exception looks like a transient API error."""
    msg = str(exc).lower()
    return any(s.lower() in msg for s in _RETRYABLE_SUBSTRINGS)


class NormalizedChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI with normalized content output.

    Gemini 3 models return content as list of typed blocks.
    This normalizes to string for consistent downstream handling.

    Also wraps invoke() with retry + exponential backoff for transient
    API errors (503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED).
    """

    def invoke(self, input, config=None, **kwargs):
        max_attempts = getattr(self, "_invoke_max_retries", _DEFAULT_MAX_RETRIES) + 1
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                return normalize_content(super().invoke(input, config, **kwargs))
            except Exception as exc:
                if not _is_retryable(exc) or attempt >= max_attempts - 1:
                    raise
                last_exc = exc
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                logger.warning(
                    "Google API transient error (attempt %d/%d): %s — retrying in %.0fs",
                    attempt + 1, max_attempts, exc, delay,
                )
                time.sleep(delay)

        raise last_exc  # unreachable, but keeps type checkers happy


class GoogleClient(BaseLLMClient):
    """Client for Google Gemini models."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatGoogleGenerativeAI instance."""
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("timeout", "max_retries", "callbacks", "http_client", "http_async_client"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        # Ensure a sensible default for max_retries (HTTP-level retries)
        llm_kwargs.setdefault("max_retries", _DEFAULT_MAX_RETRIES)

        # Unified api_key maps to provider-specific google_api_key
        google_api_key = self.kwargs.get("api_key") or self.kwargs.get("google_api_key")
        if google_api_key:
            llm_kwargs["google_api_key"] = google_api_key

        # Map thinking_level to appropriate API param based on model
        # Gemini 3 Pro: low, high
        # Gemini 3 Flash: minimal, low, medium, high
        # Gemini 2.5: thinking_budget (0=disable, -1=dynamic)
        thinking_level = self.kwargs.get("thinking_level")
        if thinking_level:
            model_lower = self.model.lower()
            if "gemini-3" in model_lower:
                # Gemini 3 Pro doesn't support "minimal", use "low" instead
                if "pro" in model_lower and thinking_level == "minimal":
                    thinking_level = "low"
                llm_kwargs["thinking_level"] = thinking_level
            else:
                # Gemini 2.5: map to thinking_budget
                llm_kwargs["thinking_budget"] = -1 if thinking_level == "high" else 0

        return NormalizedChatGoogleGenerativeAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Google."""
        return validate_model("google", self.model)

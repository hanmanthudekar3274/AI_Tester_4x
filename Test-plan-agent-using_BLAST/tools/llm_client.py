"""LLM adapter.

Interface adopted from Requirement_Analyser_Agent/src/llm/base_llm.py: system
and user prompts stay separate arguments and are never concatenated, because
concatenation defeats structured JSON output.

v1 ships one provider, Groq. The abstract base exists so a second provider is
an added file rather than an edit to the pipeline.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from . import config_store

DEFAULT_MODEL = "openai/gpt-oss-120b"

# Groq bills input and output against one tokens-per-minute budget, so a
# max_tokens larger than the whole TPM allowance is rejected with a 413 before
# any input is even counted. 8000 is the on-demand tier limit observed on this
# account; override with GROQ_TPM_LIMIT for a higher tier.
DEFAULT_TPM_LIMIT = 8000

# Headroom for the chat wrapper tokens and for estimation error, since we
# approximate token counts from character length rather than tokenizing.
TPM_SAFETY_MARGIN = 400

# Conservative characters-per-token ratio. JSON with punctuation and short keys
# tokenizes denser than prose, so this deliberately over-estimates.
CHARS_PER_TOKEN = 3.2

MIN_USEFUL_OUTPUT_TOKENS = 1500

# Defensive only. Instruction 20 in the SOP forbids fences; this strips them
# anyway rather than failing a run over a cosmetic model slip.
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


class LLMError(Exception):
    """Any failure calling or parsing an LLM response."""


class BaseLLM(ABC):
    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        json_mode: bool = True,
        extra_messages: list[dict[str, str]] | None = None,
    ) -> str:
        """Return the raw text of the model's reply."""

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Return (ok, message). Validates both the key and the model id."""

    @property
    @abstractmethod
    def name(self) -> str: ...


class GroqLLM(BaseLLM):
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        tpm_limit: int = DEFAULT_TPM_LIMIT,
    ) -> None:
        if not api_key:
            raise LLMError("Groq API key is not set. Add it in Settings.")
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.temperature = temperature
        self.tpm_limit = tpm_limit or DEFAULT_TPM_LIMIT
        self.last_usage: dict[str, Any] = {}

    def input_budget(self) -> int:
        """Characters of input that still leave room for a useful response."""
        allowance = self.tpm_limit - TPM_SAFETY_MARGIN - MIN_USEFUL_OUTPUT_TOKENS
        return max(int(allowance * CHARS_PER_TOKEN), 2000)

    @property
    def name(self) -> str:
        return f"Groq/{self.model}"

    def _client(self):
        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMError(
                "The groq package is not installed. Run: pip install groq"
            ) from exc
        return Groq(api_key=self.api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        json_mode: bool = True,
        extra_messages: list[dict[str, str]] | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if extra_messages:
            messages.extend(extra_messages)

        # Input and output share one TPM budget, so cap the reservation to what
        # is actually left after the prompt. Without this, a max_tokens near or
        # above the TPM limit is rejected with a 413 before the request even
        # runs.
        estimated_input = int(
            sum(len(m.get("content") or "") for m in messages) / CHARS_PER_TOKEN
        )
        headroom = self.tpm_limit - TPM_SAFETY_MARGIN - estimated_input

        if headroom < MIN_USEFUL_OUTPUT_TOKENS:
            raise LLMError(
                f"The request needs about {estimated_input} input tokens, which "
                f"leaves only {max(headroom, 0)} of your {self.tpm_limit} "
                "tokens-per-minute budget for the response. Shorten the issue "
                "content, or raise the limit in Settings if your Groq tier "
                "allows more."
            )

        effective_max = max(min(max_tokens, headroom), MIN_USEFUL_OUTPUT_TOKENS)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": effective_max,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        started = time.monotonic()
        try:
            response = self._client().chat.completions.create(**kwargs)
        except Exception as exc:
            raise LLMError(self._explain(exc)) from exc
        elapsed = time.monotonic() - started

        usage = getattr(response, "usage", None)
        self.last_usage = {
            "model": getattr(response, "model", self.model),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "latency_seconds": round(elapsed, 2),
        }

        if not response.choices:
            raise LLMError("Groq returned no choices in the response.")

        content = response.choices[0].message.content
        if not content or not content.strip():
            finish = getattr(response.choices[0], "finish_reason", "unknown")
            raise LLMError(
                f"Groq returned an empty response (finish_reason={finish}). "
                "If this is 'length', raise GROQ_MAX_TOKENS in Settings."
            )
        return content

    def is_available(self) -> tuple[bool, str]:
        """Validate the key, then the model id, using a single models.list().

        Membership in the returned list is the check, NOT models.retrieve().
        retrieve() puts the id into the URL path, so a namespaced id such as
        'openai/gpt-oss-120b' is encoded as 'openai%2Fgpt-oss-120b' and 404s
        even when the model is present on the account.
        """
        try:
            client = self._client()
        except LLMError as exc:
            return False, str(exc)

        try:
            listing = client.models.list()
        except Exception as exc:
            return False, f"Groq key rejected. {self._explain(exc)}"

        available = sorted(
            str(m.id) for m in (getattr(listing, "data", None) or []) if getattr(m, "id", None)
        )

        if not available:
            return True, (
                "Key is valid, but the account returned no models, so "
                f"'{self.model}' could not be confirmed."
            )

        if self.model not in available:
            close = [m for m in available if self.model.split("/")[-1] in m] or available
            return False, (
                f"Key is valid, but '{self.model}' is not on this account. "
                f"Available: {', '.join(close[:8])}"
            )

        return True, f"Connected. Model '{self.model}' is available."

    @staticmethod
    def _explain(exc: Exception) -> str:
        """Map an SDK exception to an actionable message. Never echoes the key."""
        name = exc.__class__.__name__
        text = str(exc)

        if "413" in text or "too large" in text.lower():
            return (
                "The request exceeded your Groq tokens-per-minute budget. "
                "Input and output share that budget. Lower 'Max output tokens' "
                "in Settings, or raise the tokens-per-minute limit there if "
                "your Groq tier allows more."
            )
        if "401" in text or "invalid_api_key" in text or "Authentication" in name:
            return "Authentication failed. Check the Groq API key in Settings."
        if "404" in text or "model_not_found" in text or "does not exist" in text:
            return (
                "The model id was not found on this account. Check the Model ID "
                "field in Settings."
            )
        if "429" in text or "RateLimit" in name:
            return "Groq rate limit reached. Wait and retry."
        if "Connection" in name or "Timeout" in name:
            return "Cannot reach the Groq API. Check your network connection."
        return f"{name}: {text[:200]}"


# --------------------------------------------------------------------------
# Factory and helpers
# --------------------------------------------------------------------------

def from_config(config: dict[str, str] | None = None) -> BaseLLM:
    config = config if config is not None else config_store.load_config()
    try:
        temperature = float(config.get("GROQ_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    try:
        tpm_limit = int(config.get("GROQ_TPM_LIMIT", DEFAULT_TPM_LIMIT))
    except (TypeError, ValueError):
        tpm_limit = DEFAULT_TPM_LIMIT
    return GroqLLM(
        api_key=str(config.get("GROQ_API_KEY", "")).strip(),
        model=str(config.get("GROQ_MODEL", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
        temperature=temperature,
        tpm_limit=tpm_limit,
    )


def test_connection(config: dict[str, str]) -> dict[str, Any]:
    """Settings-screen entry point. Returns a result dict, never raises."""
    try:
        llm = from_config(config)
    except LLMError as exc:
        return {"ok": False, "message": str(exc)}
    ok, message = llm.is_available()
    return {"ok": ok, "message": message, "model": llm.model}


def parse_json_response(raw: str) -> dict[str, Any]:
    """Parse a model reply into a dict, tolerating a stray code fence."""
    text = (raw or "").strip()

    fenced = _FENCE_RE.match(text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        preview = text[:200].replace("\n", " ")
        raise LLMError(
            f"The model did not return valid JSON ({exc.msg} at line {exc.lineno}). "
            f"Response began: {preview}"
        ) from exc

    if not isinstance(parsed, dict):
        raise LLMError(
            f"The model returned a JSON {type(parsed).__name__}, not an object."
        )
    return parsed

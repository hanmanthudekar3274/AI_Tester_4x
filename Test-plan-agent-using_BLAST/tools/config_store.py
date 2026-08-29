"""Read and write the project's .env file.

This is the ONLY module permitted to touch .env. Every other module reads
configuration through `load_config()` or the typed accessors below.

Design constraints from LLM.md section 8:
  - .env is the single configuration store. There is no config.json.
  - Writes preserve comments, blank lines, and key order.
  - Writes are atomic: a temp file is written and then replaced, so an
    interrupted save cannot leave a truncated .env behind.
  - Saving also updates os.environ in-process, so a "Test Connection" click
    immediately after a "Save" click uses the new value without a restart.
  - Secret values are never logged and never written anywhere but .env.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

# Keys whose values must never appear in logs, error messages, or the UI in
# plain form. The Settings screen renders these masked.
SECRET_KEYS = frozenset({"JIRA_API_TOKEN", "GROQ_API_KEY"})

DEFAULTS: dict[str, str] = {
    "JIRA_BASE_URL": "",
    "JIRA_EMAIL": "",
    "JIRA_API_TOKEN": "",
    "JIRA_DEFAULT_PROJECT_KEY": "",
    "JIRA_VERIFY_SSL": "true",
    "GROQ_API_KEY": "",
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_TEMPERATURE": "0.2",
    "GROQ_MAX_TOKENS": "6000",
    "GROQ_TPM_LIMIT": "8000",
    "DISPLAY_NAME": "",
    "DEFAULT_OUTPUT_FORMAT": "markdown",
}

# Settings without which the pipeline cannot run at all. The chat screen
# preflight checks these and blocks generation rather than half-running.
REQUIRED_KEYS = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "GROQ_API_KEY")


class ConfigError(Exception):
    """Raised when configuration is missing or malformed."""


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def load_config() -> dict[str, str]:
    """Return the full configuration: defaults, then process environment, then
    .env.

    The .env file wins over os.environ for any key it actually defines with a
    value. That ordering matters because the file is hand-editable: once a key
    has been saved through the Settings screen it also lives in os.environ, and
    if os.environ won, a later manual edit to .env would be silently ignored.

    Keys absent from .env still fall through to os.environ, so CI and container
    deployments that set real environment variables and ship no .env keep
    working.
    """
    config = dict(DEFAULTS)

    for key in DEFAULTS:
        env_value = os.environ.get(key)
        if env_value:
            config[key] = env_value

    if ENV_FILE.exists():
        stored = dotenv_values(ENV_FILE)
        config.update({k: v for k, v in stored.items() if v})

    return config


def get(key: str, default: str = "") -> str:
    return load_config().get(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    raw = get(key, "true" if default else "false").strip().lower()
    return raw in ("1", "true", "yes", "on")


def get_float(key: str, default: float) -> float:
    try:
        return float(get(key, str(default)))
    except ValueError:
        return default


def get_int(key: str, default: int) -> int:
    try:
        return int(get(key, str(default)))
    except ValueError:
        return default


def missing_required(config: dict[str, str] | None = None) -> list[str]:
    """Return the required keys that are empty. Empty list means ready to run."""
    config = config if config is not None else load_config()
    return [key for key in REQUIRED_KEYS if not str(config.get(key, "")).strip()]


def mask(value: str) -> str:
    """Render a secret for display. Never returns the full value."""
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * 12}{value[-4:]}"


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def save_config(updates: dict[str, str]) -> None:
    """Merge `updates` into .env and into os.environ.

    Existing comments, blank lines, and key order are preserved. Keys not
    already present are appended. Values are written verbatim after stripping
    surrounding whitespace, and are quoted only when they contain a character
    that would otherwise break parsing.
    """
    cleaned = {k: str(v).strip() for k, v in updates.items()}

    lines = _read_lines()
    seen: set[str] = set()
    out: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append(line)
            continue

        key = stripped.split("=", 1)[0].strip()
        if key in cleaned:
            out.append(f"{key}={_quote(cleaned[key])}")
            seen.add(key)
        else:
            out.append(line)

    new_keys = [k for k in cleaned if k not in seen]
    if new_keys:
        if out and out[-1].strip():
            out.append("")
        for key in new_keys:
            out.append(f"{key}={_quote(cleaned[key])}")

    _atomic_write("\n".join(out) + "\n")

    # Reflect the change in this process so a Test Connection immediately
    # after a Save sees the new value.
    for key, value in cleaned.items():
        os.environ[key] = value


def _read_lines() -> list[str]:
    """Return the current .env as lines, seeding from .env.example on first run."""
    if ENV_FILE.exists():
        return ENV_FILE.read_text(encoding="utf-8").splitlines()
    if ENV_EXAMPLE.exists():
        return ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    return []


def _quote(value: str) -> str:
    """Quote only when necessary, to keep .env readable."""
    if value == "":
        return ""
    if any(ch in value for ch in ' #"\'\n\t'):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _atomic_write(content: str) -> None:
    """Write .env via a temp file and replace, so an interrupted write cannot
    truncate an existing .env and lose the user's credentials."""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(ENV_FILE.parent), prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, ENV_FILE)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        # Best effort. Windows ignores POSIX modes; the file is gitignored either way.
        pass


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------

def init() -> None:
    """Load .env into the process environment. Call once at app start."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)

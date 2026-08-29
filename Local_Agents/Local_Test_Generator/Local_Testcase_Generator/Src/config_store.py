import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULTS = {
    "llm_model": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 4096,
}


def load_config() -> dict:
    base = dict(DEFAULTS)
    if not CONFIG_FILE.exists():
        return base
    try:
        stored = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        base.update(stored)
        return base
    except (json.JSONDecodeError, OSError):
        return base


def save_config(data: dict) -> None:
    existing = load_config()
    existing.update(data)
    CONFIG_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def get(key: str, default=None):
    return load_config().get(key, default)

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PROVIDER = "OpenRouter"
DEFAULT_MODEL = "openai/gpt-4.1-mini"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.2


@dataclass(slots=True)
class AhuraConfig:
    provider: str
    model: str
    api_key_present: bool
    api_key_name: str
    session_dir: Path
    max_tokens: int
    temperature: float


def get_session_dir() -> Path:
    home = Path.home()
    session_dir = home / ".ahura" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def load_config() -> AhuraConfig:
    api_key_name = "OPENROUTER_API_KEY"
    api_key = os.getenv(api_key_name)

    provider = os.getenv("AHURA_PROVIDER", DEFAULT_PROVIDER)
    model = os.getenv("AHURA_MODEL", DEFAULT_MODEL)
    session_dir = get_session_dir()

    max_tokens_raw = os.getenv("AHURA_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))
    temperature_raw = os.getenv("AHURA_TEMPERATURE", str(DEFAULT_TEMPERATURE))

    try:
        max_tokens = int(max_tokens_raw)
    except ValueError:
        max_tokens = DEFAULT_MAX_TOKENS

    try:
        temperature = float(temperature_raw)
    except ValueError:
        temperature = DEFAULT_TEMPERATURE

    return AhuraConfig(
        provider=provider,
        model=model,
        api_key_present=bool(api_key),
        api_key_name=api_key_name,
        session_dir=session_dir,
        max_tokens=max_tokens,
        temperature=temperature,
    )

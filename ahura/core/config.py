from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PROVIDER = "OpenRouter"
DEFAULT_MODEL = "openai/gpt-4.1-mini"


@dataclass(slots=True)
class AhuraConfig:
    provider: str
    model: str
    api_key_present: bool
    api_key_name: str
    session_dir: Path


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

    return AhuraConfig(
        provider=provider,
        model=model,
        api_key_present=bool(api_key),
        api_key_name=api_key_name,
        session_dir=session_dir,
    )

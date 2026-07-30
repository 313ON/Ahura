from __future__ import annotations

import os
from pathlib import Path

from ahura.chat.constants import LAST_SESSION_POINTER


def get_ahura_base_dir() -> Path:
    """
    Resolve Ahura base directory.

    Priority:
    1. HOME/.ahura
    2. USERPROFILE/.ahura
    3. cwd/.ahura
    """
    home = os.environ.get("HOME")
    if home:
        return Path(home) / ".ahura"

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        return Path(userprofile) / ".ahura"

    return Path.cwd() / ".ahura"


def get_sessions_dir() -> Path:
    return get_ahura_base_dir() / "sessions"


def get_logs_dir() -> Path:
    return get_ahura_base_dir() / "logs"


def get_cache_dir() -> Path:
    return get_ahura_base_dir() / "cache"


def get_config_dir() -> Path:
    return get_ahura_base_dir() / "config"


def get_last_session_pointer_path() -> Path:
    return get_sessions_dir() / LAST_SESSION_POINTER


def ensure_ahura_dirs() -> None:
    for path in (
        get_ahura_base_dir(),
        get_sessions_dir(),
        get_logs_dir(),
        get_cache_dir(),
        get_config_dir(),
    ):
        path.mkdir(parents=True, exist_ok=True)

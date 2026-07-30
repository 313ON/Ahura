from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .model_router import ModelProfile


def load_profiles_from_file(path: Path) -> List[ModelProfile]:
    data = json.loads(path.read_text(encoding="utf-8"))
    profiles_raw = data.get("profiles") or []

    profiles: List[ModelProfile] = []
    for item in profiles_raw:
        profiles.append(
            ModelProfile(
                name=item["name"],
                primary=item["primary"],
                fallbacks=item.get("fallbacks") or [],
            )
        )

    return profiles

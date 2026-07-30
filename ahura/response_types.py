from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AssistantResult:
    ok: bool
    text: str
    model: str | None = None
    error_type: str | None = None
    message: str | None = None
    raw: object | None = None

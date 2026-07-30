from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ahura.chat.constants import DEFAULT_SCHEMA_VERSION


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 UTC format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ChatMessage:
    """Canonical in-memory chat record."""
    role: str
    content: str
    ts: str = field(default_factory=utc_now_iso)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "role": self.role,
            "content": self.content,
            "meta": self.meta,
        }

    @classmethod
    def from_record(cls, data: dict[str, Any]) -> "ChatMessage":
        return cls(
            role=str(data.get("role", "")),
            content=str(data.get("content", "")),
            ts=str(data.get("ts", utc_now_iso())),
            meta=dict(data.get("meta", {})),
        )

    @property
    def is_reset_event(self) -> bool:
        return self.meta.get("event") == "reset"

    @property
    def is_file_summary(self) -> bool:
        return self.meta.get("kind") == "file_summary"


@dataclass(slots=True)
class SessionMetadata:
    """Persistent session metadata."""
    session_id: str
    created_at: str
    model_policy: dict[str, Any] = field(default_factory=lambda: {
        "fallback": True,
        "preferred": None,
    })
    system_prompt: str = ""
    files_attached: list[str] = field(default_factory=list)
    schema_version: str = DEFAULT_SCHEMA_VERSION

    def to_record(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "model_policy": self.model_policy,
            "system_prompt": self.system_prompt,
            "files_attached": self.files_attached,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_record(cls, data: dict[str, Any]) -> "SessionMetadata":
        return cls(
            session_id=str(data.get("session_id", "")),
            created_at=str(data.get("created_at", utc_now_iso())),
            model_policy=dict(data.get("model_policy", {"fallback": True, "preferred": None})),
            system_prompt=str(data.get("system_prompt", "")),
            files_attached=list(data.get("files_attached", [])),
            schema_version=str(data.get("schema_version", DEFAULT_SCHEMA_VERSION)),
        )


@dataclass(slots=True)
class SessionState:
    """Full in-memory session state."""
    metadata: SessionMetadata
    messages: list[ChatMessage] = field(default_factory=list)

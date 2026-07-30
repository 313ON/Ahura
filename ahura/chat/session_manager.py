from __future__ import annotations

import json
import os
from pathlib import Path

from ahura.chat.constants import DEFAULT_SYSTEM_PROMPT, RESET_EVENT_TYPE
from ahura.chat.models import ChatMessage, SessionMetadata, SessionState, utc_now_iso
from ahura.chat.redaction import redact_text


class SessionManager:
    """
    Manage Ahura sessions with JSONL persistence.

    Guarantees:
    - append-friendly JSONL persistence
    - atomic metadata writes
    - graceful recovery from malformed trailing lines
    - reset-aware transcript semantics
    """

    def __init__(self, sessions_dir: Path, last_session_pointer: Path) -> None:
        self.sessions_dir = sessions_dir
        self.last_session_pointer = last_session_pointer
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._state: SessionState | None = None
        self._session_path: Path | None = None
        self._meta_path: Path | None = None

    @property
    def state(self) -> SessionState:
        if self._state is None:
            raise RuntimeError("No active session.")
        return self._state

    @property
    def current_session_id(self) -> str:
        return self.state.metadata.session_id

    @property
    def current_system_prompt(self) -> str:
        return self.state.metadata.system_prompt

    def _build_session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"session_{session_id}.jsonl"

    def _build_meta_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"session_{session_id}.meta.json"

    def _write_last_session_pointer(self, session_id: str) -> None:
        temp_path = self.last_session_pointer.with_suffix(".tmp")
        temp_path.write_text(session_id, encoding="utf-8")
        os.replace(temp_path, self.last_session_pointer)

    def read_last_session_id(self) -> str | None:
        if not self.last_session_pointer.exists():
            return None
        value = self.last_session_pointer.read_text(encoding="utf-8").strip()
        return value or None

    def start_new_session(
        self,
        session_id: str,
        *,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        preferred_model: str | None = None,
        fallback_enabled: bool = True,
    ) -> SessionState:
        metadata = SessionMetadata(
            session_id=session_id,
            created_at=utc_now_iso(),
            model_policy={
                "fallback": fallback_enabled,
                "preferred": preferred_model,
            },
            system_prompt=redact_text(system_prompt),
            files_attached=[],
        )
        self._state = SessionState(metadata=metadata, messages=[])
        self._session_path = self._build_session_path(session_id)
        self._meta_path = self._build_meta_path(session_id)
        self.save_metadata()
        self._write_last_session_pointer(session_id)
        return self._state

    def load_session(self, session_id: str) -> SessionState:
        session_path = self._build_session_path(session_id)
        meta_path = self._build_meta_path(session_id)

        if not session_path.exists():
            raise FileNotFoundError(f"Session not found: {session_path}")

        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as f:
                metadata = SessionMetadata.from_record(json.load(f))
        else:
            metadata = SessionMetadata(
                session_id=session_id,
                created_at=utc_now_iso(),
                system_prompt=DEFAULT_SYSTEM_PROMPT,
            )

        messages: list[ChatMessage] = []
        with session_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                messages.append(ChatMessage.from_record(record))

        self._state = SessionState(metadata=metadata, messages=messages)
        self._session_path = session_path
        self._meta_path = meta_path
        self._write_last_session_pointer(session_id)
        return self._state

    def save_metadata(self) -> None:
        if self._meta_path is None:
            raise RuntimeError("Session metadata path is not initialized.")
        payload = self.state.metadata.to_record()
        payload["system_prompt"] = redact_text(str(payload.get("system_prompt", "")))

        temp_path = self._meta_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, self._meta_path)

    def _append_record_to_jsonl(self, record: dict) -> None:
        if self._session_path is None:
            raise RuntimeError("Session path is not initialized.")
        safe_record = dict(record)
        safe_record["content"] = redact_text(str(safe_record.get("content", "")))
        line = json.dumps(safe_record, ensure_ascii=False)
        with self._session_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _append_message(self, role: str, content: str, meta: dict | None = None) -> ChatMessage:
        safe_content = redact_text(content)
        message = ChatMessage(role=role, content=safe_content, meta=meta or {})
        self.state.messages.append(message)
        self._append_record_to_jsonl(message.to_record())
        return message

    def add_user_message(self, content: str, *, source: str = "repl") -> ChatMessage:
        return self._append_message("user", content, meta={"source": source})

    def add_assistant_message(self, content: str, *, model: str | None = None) -> ChatMessage:
        meta: dict[str, str] = {}
        if model:
            meta["model"] = model
        return self._append_message("assistant", content, meta=meta)

    def add_file_summary_message(self, summary: str, *, path: str) -> ChatMessage:
        return self._append_message(
            "system",
            summary,
            meta={"kind": "file_summary", "path": path},
        )

    def add_reset_event(self) -> ChatMessage:
        return self._append_message(
            "system",
            "[[context reset]]",
            meta={"event": RESET_EVENT_TYPE},
        )

    def save_all(self) -> None:
        if self._session_path is None:
            raise RuntimeError("Session path is not initialized.")
        with self._session_path.open("w", encoding="utf-8") as f:
            for msg in self.state.messages:
                record = msg.to_record()
                record["content"] = redact_text(str(record.get("content", "")))
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.save_metadata()

    def reset_context(self) -> None:
        self.add_reset_event()

    def set_system_prompt(self, text: str) -> None:
        self.state.metadata.system_prompt = redact_text(text)
        self.save_metadata()

    def attach_file(self, path: str) -> None:
        if path not in self.state.metadata.files_attached:
            self.state.metadata.files_attached.append(path)
            self.save_metadata()

    def set_preferred_model(self, model: str | None, *, fallback_enabled: bool) -> None:
        self.state.metadata.model_policy = {
            "fallback": fallback_enabled,
            "preferred": model,
        }
        self.save_metadata()

    def get_reset_scoped_messages(self) -> list[ChatMessage]:
        last_reset_index = -1
        for idx, msg in enumerate(self.state.messages):
            if msg.is_reset_event:
                last_reset_index = idx
        if last_reset_index < 0:
            return list(self.state.messages)
        return list(self.state.messages[last_reset_index + 1 :])

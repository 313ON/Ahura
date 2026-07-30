from __future__ import annotations

from ahura.chat.constants import DEFAULT_MAX_CONTEXT_CHARS
from ahura.chat.session_manager import SessionManager


class ContextBuilder:
    """
    Build model-ready messages from session state.

    Rules:
    - preserve system prompt
    - preserve file summaries after latest reset
    - keep latest conversational turns within char budget
    """

    def __init__(self, max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> None:
        self.max_context_chars = max_context_chars

    def build_messages(self, session_manager: SessionManager) -> list[dict[str, str]]:
        scoped_messages = session_manager.get_reset_scoped_messages()
        output: list[dict[str, str]] = []

        system_prompt = session_manager.current_system_prompt.strip()
        if system_prompt:
            output.append({"role": "system", "content": system_prompt})

        file_summaries = [m for m in scoped_messages if m.is_file_summary]
        conversational = [m for m in scoped_messages if not m.is_file_summary]

        for msg in file_summaries:
            output.append({"role": msg.role, "content": msg.content})

        budget_used = sum(len(m["content"]) for m in output)

        tail: list[dict[str, str]] = []
        for msg in reversed(conversational):
            msg_len = len(msg.content)
            if budget_used + msg_len > self.max_context_chars:
                break
            tail.append({"role": msg.role, "content": msg.content})
            budget_used += msg_len

        output.extend(reversed(tail))
        return output

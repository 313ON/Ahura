from __future__ import annotations

from dataclasses import dataclass

from ahura.core.provider import ChatMessage, OpenRouterClient


@dataclass(slots=True)
class ChatService:
    """Application service for conversational requests."""

    client: OpenRouterClient
    system_prompt: str = (
        "You are Ahura, a concise and reliable CLI AI assistant for IT and systems work."
    )

    def ask(self, user_text: str) -> str:
        """Send a single-turn prompt and return the assistant response."""
        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(role="user", content=user_text),
        ]
        return self.client.chat(messages)

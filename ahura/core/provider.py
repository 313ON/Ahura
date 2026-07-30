from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    """Raised when the upstream provider request fails."""


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class OpenRouterClient:
    """Minimal OpenRouter chat completions client."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url

    def chat(self, messages: list[ChatMessage]) -> str:
        """Send chat messages to OpenRouter and return assistant text."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
        }

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.base_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost/ahura",
                "X-Title": "Ahura CLI",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(
                f"OpenRouter HTTP {exc.code}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"Network error: {exc.reason}") from exc
        except Exception as exc:
            raise ProviderError(f"Unexpected provider error: {exc}") from exc

        try:
            parsed = json.loads(raw_response)
            return parsed["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ProviderError(
                f"Malformed provider response: {raw_response}"
            ) from exc

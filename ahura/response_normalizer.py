from __future__ import annotations

from typing import Any

from ahura.response_types import AssistantResult


class ResponseNormalizer:
    @classmethod
    def normalize(cls, payload: object, *, model: str | None = None) -> AssistantResult:
        if payload is None or payload == "" or payload == [] or payload == {}:
            return AssistantResult(
                ok=False,
                text="",
                model=model,
                error_type="empty_response",
                message="Provider returned an empty response.",
                raw=payload,
            )

        if isinstance(payload, str):
            return AssistantResult(ok=True, text=payload, model=model, raw=payload)

        if not isinstance(payload, dict):
            return AssistantResult(
                ok=False,
                text="",
                model=model,
                error_type="malformed_response",
                message=f"Unexpected provider response type: {type(payload).__name__}.",
                raw=payload,
            )

        resolved_model = cls._string_or_none(payload.get("model")) or model
        if "error" in payload and payload["error"] is not None:
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="provider_error",
                message=cls.error_message(payload["error"]),
                raw=payload,
            )

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="malformed_response",
                message="Provider response did not contain a usable choice.",
                raw=payload,
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="malformed_response",
                message="Provider returned a malformed choice.",
                raw=payload,
            )

        if first_choice.get("finish_reason") == "error":
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="provider_error",
                message="Provider reported an error finish reason.",
                raw=payload,
            )

        message = first_choice.get("message")
        if not isinstance(message, dict):
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="malformed_response",
                message="Provider choice did not contain a message object.",
                raw=payload,
            )

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            return AssistantResult(
                ok=False,
                text="",
                model=resolved_model,
                error_type="malformed_response",
                message="Provider message did not contain text content.",
                raw=payload,
            )

        return AssistantResult(ok=True, text=content, model=resolved_model, raw=payload)

    @staticmethod
    def object_or_empty(payload: object) -> dict[str, Any]:
        return payload if isinstance(payload, dict) else {}

    @classmethod
    def nested_object(cls, payload: object, key: str) -> dict[str, Any]:
        value = cls.object_or_empty(payload).get(key)
        return value if isinstance(value, dict) else {}

    @classmethod
    def error_message(cls, error: object, default: str = "Provider request failed.") -> str:
        if isinstance(error, str):
            return error.strip() or default
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
            return str(error)
        if error is None:
            return default
        return str(error)

    @staticmethod
    def _string_or_none(value: object) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

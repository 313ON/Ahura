from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .openrouter_client import (
    OpenRouterClient,
    OpenRouterCreditError,
    OpenRouterRateLimitError,
    OpenRouterError,
    KeyLimits,
)


@dataclass
class ModelProfile:
    """Routing profile: primary + ordered fallbacks."""
    name: str
    primary: str
    fallbacks: List[str]

    def chain(self) -> List[str]:
        return [self.primary] + self.fallbacks


@dataclass
class RoutedResponse:
    """Wrapper for router results."""
    profile_name: str
    model_used: str
    response: Dict[str, Any]
    key_limits_snapshot: Optional[KeyLimits]


class AhuraModelRouter:
    """
    High-level router over OpenRouterClient.
    """

    def __init__(
        self,
        client: OpenRouterClient,
        profiles: List[ModelProfile],
        *,
        proactive_limit_check: bool = True,
        default_profile_name: str = "default",
        rate_limit_backoff_seconds: float = 2.0,
        max_rate_limit_retries: int = 3,
    ) -> None:
        self.client = client
        self._profiles: Dict[str, ModelProfile] = {p.name: p for p in profiles}
        self.proactive_limit_check = proactive_limit_check
        self.default_profile_name = default_profile_name
        self.rate_limit_backoff_seconds = rate_limit_backoff_seconds
        self.max_rate_limit_retries = max_rate_limit_retries

    def get_profile(self, name: Optional[str]) -> ModelProfile:
        profile_name = name or self.default_profile_name
        try:
            return self._profiles[profile_name]
        except KeyError as exc:
            raise ValueError(f"Unknown model profile: {profile_name}") from exc

    def _should_avoid_paid(self, limits: KeyLimits) -> bool:
        return not limits.can_spend()

    def route_chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        profile_name: Optional[str] = None,
        plugins: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> RoutedResponse:
        profile = self.get_profile(profile_name)

        key_limits_snapshot: Optional[KeyLimits] = None
        avoid_paid = False

        if self.proactive_limit_check:
            try:
                key_limits_snapshot = self.client.get_key_limits()
                avoid_paid = self._should_avoid_paid(key_limits_snapshot)
            except OpenRouterError:
                key_limits_snapshot = None

        candidate_chain = profile.chain()
        if avoid_paid:
            candidate_chain = [
                m for m in candidate_chain
                if m.endswith(":free") or "free" in m.lower()
            ] or candidate_chain

        last_error: Optional[Exception] = None

        for model_id in candidate_chain:
            try:
                response = self.client.chat_completion(
                    model=model_id,
                    messages=messages,
                    stream=False,
                    plugins=plugins,
                    response_format=response_format,
                    extra_params=extra_params,
                )

                choices = response.get("choices") or []
                if choices:
                    finish_reason = choices[0].get("finish_reason")
                    if finish_reason == "error":
                        last_error = OpenRouterError(
                            f"Model {model_id} returned finish_reason=error"
                        )
                        continue

                return RoutedResponse(
                    profile_name=profile.name,
                    model_used=model_id,
                    response=response,
                    key_limits_snapshot=key_limits_snapshot,
                )

            except OpenRouterCreditError as exc:
                last_error = exc
                continue

            except OpenRouterRateLimitError as exc:
                last_error = exc
                success = self._retry_same_model(
                    model_id=model_id,
                    messages=messages,
                    plugins=plugins,
                    response_format=response_format,
                    extra_params=extra_params,
                    initial_error=exc,
                )
                if success is not None:
                    return RoutedResponse(
                        profile_name=profile.name,
                        model_used=model_id,
                        response=success,
                        key_limits_snapshot=key_limits_snapshot,
                    )
                continue

            except OpenRouterError as exc:
                last_error = exc
                continue

        raise RuntimeError(
            f"All models in profile '{profile.name}' failed"
        ) from last_error

    def _retry_same_model(
        self,
        *,
        model_id: str,
        messages: List[Dict[str, Any]],
        plugins: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        initial_error: OpenRouterRateLimitError,
    ) -> Optional[Dict[str, Any]]:
        backoff = self.rate_limit_backoff_seconds
        if initial_error.retry_after and initial_error.retry_after > backoff:
            backoff = initial_error.retry_after

        for _ in range(self.max_rate_limit_retries):
            time.sleep(backoff)
            backoff *= 2.0

            try:
                return self.client.chat_completion(
                    model=model_id,
                    messages=messages,
                    stream=False,
                    plugins=plugins,
                    response_format=response_format,
                    extra_params=extra_params,
                )
            except OpenRouterRateLimitError:
                continue
            except OpenRouterError:
                return None

        return None

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import urllib.parse
import urllib.request
import urllib.error


class OpenRouterError(Exception):
    """Base exception for OpenRouter client errors."""


class OpenRouterRateLimitError(OpenRouterError):
    """Raised when a 429 rate limit is hit."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[float] = None,
        rate_limit_limit: Optional[int] = None,
        rate_limit_remaining: Optional[int] = None,
        rate_limit_reset: Optional[str] = None,
        raw_error: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.rate_limit_limit = rate_limit_limit
        self.rate_limit_remaining = rate_limit_remaining
        self.rate_limit_reset = rate_limit_reset
        self.raw_error = raw_error or {}


class OpenRouterCreditError(OpenRouterError):
    """Raised when a 402 credit limit / balance issue occurs."""


@dataclass
class KeyLimits:
    label: str
    limit: Optional[float]
    limit_reset: Optional[str]
    limit_remaining: Optional[float]
    include_byok_in_limit: bool
    usage: float
    usage_daily: float
    usage_weekly: float
    usage_monthly: float
    byok_usage: float
    byok_usage_daily: float
    byok_usage_weekly: float
    byok_usage_monthly: float
    is_free_tier: bool

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "KeyLimits":
        data = payload.get("data") or {}
        return cls(
            label=data.get("label", ""),
            limit=data.get("limit"),
            limit_reset=data.get("limit_reset"),
            limit_remaining=data.get("limit_remaining"),
            include_byok_in_limit=data.get("include_byok_in_limit", False),
            usage=data.get("usage", 0.0),
            usage_daily=data.get("usage_daily", 0.0),
            usage_weekly=data.get("usage_weekly", 0.0),
            usage_monthly=data.get("usage_monthly", 0.0),
            byok_usage=data.get("byok_usage", 0.0),
            byok_usage_daily=data.get("byok_usage_daily", 0.0),
            byok_usage_weekly=data.get("byok_usage_weekly", 0.0),
            byok_usage_monthly=data.get("byok_usage_monthly", 0.0),
            is_free_tier=data.get("is_free_tier", False),
        )

    def can_spend(self) -> bool:
        """Return True if key has remaining credit."""
        if self.limit_remaining is not None and self.limit_remaining <= 0:
            return False
        return True


@dataclass
class ModelInfo:
    id: str
    canonical_slug: str
    name: str
    description: str
    context_length: int
    pricing: Dict[str, Any]
    supported_parameters: List[str]
    output_modalities: List[str]

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "ModelInfo":
        data = payload.get("data") or payload
        arch = data.get("architecture") or {}
        return cls(
            id=data.get("id"),
            canonical_slug=data.get("canonical_slug", data.get("id")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            context_length=data.get("context_length", 0),
            pricing=data.get("pricing") or {},
            supported_parameters=data.get("supported_parameters") or [],
            output_modalities=arch.get("output_modalities") or [],
        )


@dataclass
class HTTPResponse:
    status_code: int
    headers: Dict[str, str]
    text: str

    def json(self) -> Any:
        return json.loads(self.text) if self.text else {}


class OpenRouterClient:
    """
    Thin client over OpenRouter REST API using Python stdlib only.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        app_referer: Optional[str] = None,
        app_title: Optional[str] = None,
        app_categories: Optional[List[str]] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        self._default_headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if app_referer:
            self._default_headers["HTTP-Referer"] = app_referer
        if app_title:
            self._default_headers["X-OpenRouter-Title"] = app_title
        if app_categories:
            self._default_headers["X-OpenRouter-Categories"] = ",".join(app_categories)

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> HTTPResponse:
        url = f"{self.base_url}{path}"

        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        merged_headers = dict(self._default_headers)
        if headers:
            merged_headers.update(headers)

        data: Optional[bytes] = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=merged_headers,
            method=method.upper(),
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                response = HTTPResponse(
                    status_code=resp.status,
                    headers=dict(resp.headers.items()),
                    text=body,
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            response = HTTPResponse(
                status_code=exc.code,
                headers=dict(exc.headers.items()) if exc.headers else {},
                text=body,
            )
        except urllib.error.URLError as exc:
            raise OpenRouterError(f"Network error: {exc}") from exc

        if response.status_code == 429:
            raw = self._safe_json(response)
            retry_after_header = response.headers.get("Retry-After")
            retry_after = float(retry_after_header) if retry_after_header else None
            raise OpenRouterRateLimitError(
                message="Rate limit exceeded",
                retry_after=retry_after,
                rate_limit_limit=self._parse_int_header(response.headers.get("X-RateLimit-Limit")),
                rate_limit_remaining=self._parse_int_header(response.headers.get("X-RateLimit-Remaining")),
                rate_limit_reset=response.headers.get("X-RateLimit-Reset"),
                raw_error=raw.get("error") if isinstance(raw, dict) else None,
            )

        if response.status_code == 402:
            raw = self._safe_json(response)
            msg = (
                (raw.get("error") or {}).get("message")
                if isinstance(raw, dict)
                else "Credit / payment required"
            )
            raise OpenRouterCreditError(msg)

        if response.status_code >= 400:
            raw = self._safe_json(response)
            msg = (
                (raw.get("error") or {}).get("message")
                if isinstance(raw, dict)
                else response.text
            )
            raise OpenRouterError(f"HTTP {response.status_code}: {msg}")

        return response

    @staticmethod
    def _safe_json(resp: HTTPResponse) -> Any:
        try:
            return resp.json()
        except Exception:
            return None

    @staticmethod
    def _parse_int_header(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def get_key_limits(self) -> KeyLimits:
        resp = self._request("GET", "/key")
        payload = resp.json()
        return KeyLimits.from_api(payload)

    def list_models(
        self,
        *,
        output_modalities: Optional[List[str]] = None,
        supported_parameters: Optional[List[str]] = None,
        sort: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if output_modalities:
            params["output_modalities"] = ",".join(output_modalities)
        if supported_parameters:
            params["supported_parameters"] = ",".join(supported_parameters)
        if sort:
            params["sort"] = sort
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        resp = self._request("GET", "/models", params=params)
        return resp.json()

    def get_model(self, model_id: str) -> ModelInfo:
        encoded_model_id = urllib.parse.quote(model_id, safe="")
        resp = self._request("GET", f"/models/{encoded_model_id}")
        payload = resp.json()
        return ModelInfo.from_api(payload)

    def chat_completion(
        self,
        *,
        model: Optional[str],
        messages: List[Dict[str, Any]],
        stream: bool = False,
        plugins: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "messages": messages,
            "stream": stream,
        }

        if model:
            body["model"] = model
        if plugins:
            body["plugins"] = plugins
        if response_format:
            body["response_format"] = response_format
        if extra_params:
            body.update(extra_params)

        resp = self._request("POST", "/chat/completions", json_body=body)
        return resp.json()

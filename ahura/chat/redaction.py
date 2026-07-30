from __future__ import annotations

import re


_RE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(OPENROUTER_API_KEY\s*=\s*)([^\s]+)", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_\-]+\b"),
    re.compile(r"(Bearer\s+)([A-Za-z0-9._\-]+)", re.IGNORECASE),
]


def redact_text(text: str) -> str:
    """Redact common secret patterns before persistence/logging."""
    redacted = text

    redacted = _RE_PATTERNS[0].sub(r"\1***REDACTED***", redacted)
    redacted = _RE_PATTERNS[1].sub("***REDACTED***", redacted)
    redacted = _RE_PATTERNS[2].sub(r"\1***REDACTED***", redacted)

    return redacted

from __future__ import annotations

from pathlib import Path

from ahura.chat.constants import DEFAULT_MAX_FILE_BYTES


def summarize_text_excerpt(text: str, *, max_chars: int = 1500) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "\n...[truncated]"


def build_file_summary(path: Path, *, max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> str:
    """
    Build a safe summary for a text-like file.
    Binary detection is intentionally conservative.
    """
    size = path.stat().st_size
    if size > max_file_bytes:
        return (
            f"Attached file: {path.name}\n"
            f"Path: {path}\n"
            f"Size: {size} bytes\n"
            "Summary mode: oversized file; full ingest skipped.\n"
        )

    raw = path.read_bytes()

    if b"\x00" in raw:
        return (
            f"Attached file: {path.name}\n"
            f"Path: {path}\n"
            f"Size: {size} bytes\n"
            "Summary mode: binary-like file detected; full ingest skipped.\n"
        )

    text = raw.decode("utf-8", errors="replace")
    excerpt = summarize_text_excerpt(text)

    return (
        f"Attached file: {path.name}\n"
        f"Path: {path}\n"
        f"Size: {size} bytes\n"
        "Summary mode: inline excerpt\n\n"
        f"{excerpt}"
    )

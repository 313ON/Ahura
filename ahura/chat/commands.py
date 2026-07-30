from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ahura.chat.file_ingest import build_file_summary
from ahura.chat.session_manager import SessionManager


@dataclass(slots=True)
class CommandResult:
    handled: bool
    should_exit: bool = False
    message: str | None = None
    enter_multiline: bool = False


def is_command(text: str) -> bool:
    return text.strip().startswith("/")


def parse_command(text: str) -> tuple[str, list[str]]:
    parts = text.strip().split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]


def handle_command(
    command: str,
    args: list[str],
    *,
    session_manager: SessionManager,
    on_model_info: Callable[[], str] | None = None,
    on_doctor: Callable[[], str] | None = None,
) -> CommandResult:
    if command == "/exit":
        return CommandResult(True, True, "خروج از Ahura.")

    if command == "/multiline":
        return CommandResult(
            True,
            False,
            "Multiline mode فعال شد. ورودی را بنویس و با /end تمام کن.",
            enter_multiline=True,
        )

    if command == "/reset":
        session_manager.reset_context()
        return CommandResult(True, False, "Context reset شد. transcript برای audit حفظ شد.")

    if command == "/save":
        session_manager.save_all()
        return CommandResult(True, False, "نشست با موفقیت ذخیره شد.")

    if command == "/load":
        if not args:
            return CommandResult(True, False, "Usage: /load <session_id>")
        session_manager.load_session(args[0])
        return CommandResult(True, False, f"نشست {args[0]} بارگذاری شد.")

    if command == "/model":
        if len(args) >= 2 and args[0] == "set":
            model_name = " ".join(args[1:]).strip()
            if not model_name:
                return CommandResult(True, False, "Usage: /model set <model>")
            session_manager.set_preferred_model(model_name, fallback_enabled=False)
            return CommandResult(True, False, f"مدل preferred روی '{model_name}' pin شد. fallback غیرفعال شد.")

        if on_model_info is not None:
            return CommandResult(True, False, on_model_info())
        return CommandResult(True, False, "Model info unavailable.")

    if command == "/models":
        policy = session_manager.state.metadata.model_policy
        return CommandResult(True, False, f"Model policy: {policy}")

    if command == "/system":
        if not args:
            current = session_manager.current_system_prompt or "(empty)"
            return CommandResult(True, False, f"Current system prompt:\n{current}")
        text = " ".join(args)
        session_manager.set_system_prompt(text)
        return CommandResult(True, False, "System prompt به‌روزرسانی شد.")

    if command == "/file":
        if not args:
            return CommandResult(True, False, "Usage: /file <path>")
        path = Path(" ".join(args))
        if not path.exists():
            return CommandResult(True, False, f"File not found: {path}")

        resolved = str(path.resolve())
        summary = build_file_summary(path.resolve())
        session_manager.attach_file(resolved)
        session_manager.add_file_summary_message(summary, path=resolved)

        return CommandResult(True, False, f"فایل attach و summary inject شد: {resolved}")

    if command == "/doctor":
        if on_doctor is not None:
            return CommandResult(True, False, on_doctor())
        return CommandResult(True, False, f"Doctor OK | session={session_manager.current_session_id}")

    if command == "/help":
        return CommandResult(
            True,
            False,
            (
                "Commands:\n"
                "  /exit\n"
                "  /multiline\n"
                "  /reset\n"
                "  /save\n"
                "  /load <session_id>\n"
                "  /model\n"
                "  /model set <model>\n"
                "  /models\n"
                "  /system\n"
                "  /system <text>\n"
                "  /file <path>\n"
                "  /doctor\n"
                "  /help\n\n"
                "Multiline input:\n"
                "  - End a line with \\ for continuation\n"
                "  - Or use /multiline and finish with /end"
            ),
        )

    return CommandResult(True, False, f"Unknown command: {command}")

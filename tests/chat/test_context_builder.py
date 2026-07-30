from pathlib import Path

from ahura.chat.context_builder import ContextBuilder
from ahura.chat.session_manager import SessionManager


def make_manager(tmp_path: Path) -> SessionManager:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    last_pointer = sessions_dir / "last_session.txt"
    return SessionManager(sessions_dir, last_pointer)


def test_build_messages_includes_system_prompt(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("ctx_001", system_prompt="system-x")
    manager.add_user_message("hello")

    builder = ContextBuilder()
    result = builder.build_messages(manager)

    assert result[0]["role"] == "system"
    assert result[0]["content"] == "system-x"


def test_build_messages_is_reset_aware(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("ctx_002")
    manager.add_user_message("old")
    manager.reset_context()
    manager.add_user_message("new")

    builder = ContextBuilder()
    result = builder.build_messages(manager)

    contents = [item["content"] for item in result]
    assert "old" not in contents
    assert "new" in contents


def test_build_messages_preserves_file_summary(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("ctx_003", system_prompt="sys")
    manager.add_file_summary_message("summary-1", path="D:/x.txt")
    manager.add_user_message("question")

    builder = ContextBuilder()
    result = builder.build_messages(manager)

    contents = [item["content"] for item in result]
    assert "summary-1" in contents
    assert "question" in contents


def test_build_messages_respects_char_budget(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("ctx_004", system_prompt="sys")
    manager.add_user_message("A" * 20)
    manager.add_assistant_message("B" * 20)
    manager.add_user_message("C" * 20)

    builder = ContextBuilder(max_context_chars=30)
    result = builder.build_messages(manager)

    contents = [item["content"] for item in result]
    assert "C" * 20 in contents

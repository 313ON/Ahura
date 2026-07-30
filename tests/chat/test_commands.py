from pathlib import Path

from ahura.chat.commands import handle_command
from ahura.chat.session_manager import SessionManager


def make_manager(tmp_path: Path) -> SessionManager:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    last_pointer = sessions_dir / "last_session.txt"
    manager = SessionManager(sessions_dir, last_pointer)
    manager.start_new_session("cmd_001")
    return manager


def test_system_without_args_shows_current_prompt(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    result = handle_command("/system", [], session_manager=manager)
    assert result.handled is True
    assert "Current system prompt:" in (result.message or "")


def test_system_with_args_updates_prompt(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    result = handle_command("/system", ["hello", "world"], session_manager=manager)
    assert result.handled is True
    assert manager.current_system_prompt == "hello world"


def test_load_without_args_returns_usage(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    result = handle_command("/load", [], session_manager=manager)
    assert "Usage: /load <session_id>" == result.message


def test_file_command_attaches_and_injects_summary(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    sample = tmp_path / "note.txt"
    sample.write_text("hello from file", encoding="utf-8")

    result = handle_command("/file", [str(sample)], session_manager=manager)

    assert result.handled is True
    assert str(sample.resolve()) in manager.state.metadata.files_attached
    assert any(msg.meta.get("kind") == "file_summary" for msg in manager.state.messages)

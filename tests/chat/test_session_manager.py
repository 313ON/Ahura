from pathlib import Path

from ahura.chat.session_manager import SessionManager


def make_manager(tmp_path: Path) -> SessionManager:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    last_pointer = sessions_dir / "last_session.txt"
    return SessionManager(sessions_dir, last_pointer)


def test_start_new_session_writes_meta_and_pointer(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("sess_001")

    assert manager.current_session_id == "sess_001"
    assert (tmp_path / "sessions" / "session_sess_001.meta.json").exists()
    assert (tmp_path / "sessions" / "last_session.txt").read_text(encoding="utf-8").strip() == "sess_001"


def test_add_messages_persists_jsonl(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("sess_002")

    manager.add_user_message("hello")
    manager.add_assistant_message("world", model="demo-model")

    jsonl_path = tmp_path / "sessions" / "session_sess_002.jsonl"
    content = jsonl_path.read_text(encoding="utf-8")

    assert '"role": "user"' in content
    assert '"role": "assistant"' in content
    assert 'demo-model' in content


def test_load_session_skips_malformed_trailing_line(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("sess_003")
    manager.add_user_message("first")
    session_file = tmp_path / "sessions" / "session_sess_003.jsonl"

    with session_file.open("a", encoding="utf-8") as f:
        f.write('{"bad_json": \n')

    loaded = make_manager(tmp_path)
    loaded.load_session("sess_003")

    assert len(loaded.state.messages) == 1
    assert loaded.state.messages[0].content == "first"


def test_reset_adds_event_not_truncate(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("sess_004")
    manager.add_user_message("before reset")
    manager.reset_context()
    manager.add_user_message("after reset")

    assert len(manager.state.messages) == 3
    assert manager.state.messages[1].meta["event"] == "reset"

    scoped = manager.get_reset_scoped_messages()
    assert len(scoped) == 1
    assert scoped[0].content == "after reset"


def test_system_prompt_is_redacted_before_persist(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.start_new_session("sess_005")
    manager.set_system_prompt("Bearer abc123 OPENROUTER_API_KEY=secret")

    meta_path = tmp_path / "sessions" / "session_sess_005.meta.json"
    content = meta_path.read_text(encoding="utf-8")

    assert "abc123" not in content
    assert "secret" not in content
    assert "***REDACTED***" in content

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from ahura.chat.commands import handle_command, is_command, parse_command
from ahura.chat.constants import DEFAULT_SYSTEM_PROMPT
from ahura.chat.context_builder import ContextBuilder
from ahura.chat.multiline import read_block_input, read_multiline_input
from ahura.chat.session_manager import SessionManager
from ahura.chat.session_paths import (
    ensure_ahura_dirs,
    get_last_session_pointer_path,
    get_sessions_dir,
)
from ahura.model_router import AhuraModelRouter
from ahura.openrouter_client import OpenRouterClient
from ahura.router_config import load_profiles_from_file
from ahura.response_types import AssistantResult
from ahura.ui_render import AhuraRenderer


def build_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_router(api_key: str) -> AhuraModelRouter:
    config_path = Path("ahura_router.json")
    profiles = load_profiles_from_file(config_path)
    client = OpenRouterClient(api_key=api_key, app_title="Ahura-CLI")
    return AhuraModelRouter(client, profiles)


def resolve_session_mode(session_manager: SessionManager, session_mode: str) -> str:
    if session_mode == "new":
        return build_session_id()

    if session_mode == "last":
        last_id = session_manager.read_last_session_id()
        if not last_id:
            raise RuntimeError("No last session pointer found.")
        return last_id

    if session_mode.startswith("load:"):
        session_id = session_mode.removeprefix("load:").strip()
        if not session_id:
            raise RuntimeError("Invalid session mode. Expected load:<session_id>")
        return session_id

    raise RuntimeError(f"Unknown session mode: {session_mode}")


def init_session(session_manager: SessionManager, session_mode: str) -> None:
    resolved = resolve_session_mode(session_manager, session_mode)

    if session_mode == "new":
        session_manager.start_new_session(
            session_id=resolved,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            preferred_model=None,
            fallback_enabled=True,
        )
        return

    session_manager.load_session(resolved)


def build_doctor_report(session_manager: SessionManager) -> str:
    state = session_manager.state
    return (
        "Doctor OK\n"
        f"  session_id: {state.metadata.session_id}\n"
        f"  schema_version: {state.metadata.schema_version}\n"
        f"  fallback_policy: {state.metadata.model_policy}\n"
        f"  files_attached: {len(state.metadata.files_attached)}\n"
        f"  messages_in_transcript: {len(state.messages)}\n"
    )


def collect_user_input() -> str:
    raw = input("\nAhura > ").rstrip()
    if not raw:
        return ""

    if raw.endswith("\\"):
        return read_multiline_input(raw)

    return raw


def run_chat_loop(session_mode: str) -> None:
    renderer = AhuraRenderer()
    renderer.welcome()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        renderer.error(
            AssistantResult(
                ok=False,
                text="",
                error_type="configuration_error",
                message="OPENROUTER_API_KEY is not set.",
            )
        )
        sys.exit(1)

    ensure_ahura_dirs()
    router = build_router(api_key)

    session_manager = SessionManager(
        get_sessions_dir(),
        get_last_session_pointer_path(),
    )
    context_builder = ContextBuilder()

    init_session(session_manager, session_mode)

    profile = router.get_profile("default")
    session_path = session_manager.sessions_dir / (
        f"session_{session_manager.current_session_id}.jsonl"
    )
    renderer.status(model=profile.primary, session_path=session_path)
    renderer.info("Ready · /help for commands · autosave enabled")

    while True:
        try:
            user_input = collect_user_input()
            if not user_input:
                continue

            if is_command(user_input):
                command, args = parse_command(user_input)
                if command == "/help":
                    renderer.help()
                    continue
                if command == "/clear":
                    renderer.clear()
                    continue
                command_result = handle_command(
                    command,
                    args,
                    session_manager=session_manager,
                    on_model_info=lambda: f"Model policy: {session_manager.state.metadata.model_policy}",
                    on_doctor=lambda: build_doctor_report(session_manager),
                )
                if command_result.message:
                    renderer.command(command_result.message)

                if command_result.enter_multiline:
                    user_input = read_block_input()
                else:
                    if command_result.should_exit:
                        break
                    continue

                if not user_input.strip():
                    continue

            session_manager.add_user_message(user_input, source="repl")
            router_messages = context_builder.build_messages(session_manager)

            profile_name = "default"
            result = router.route_chat(router_messages, profile_name=profile_name)

            if result.ok:
                session_manager.add_assistant_message(result.text, model=result.model)
                renderer.assistant(result)
            else:
                renderer.error(result)

        except KeyboardInterrupt:
            renderer.info("Interrupted")
            break
        except EOFError:
            renderer.info("EOF received · exiting")
            break
        except Exception as e:
            renderer.error(
                AssistantResult(
                    ok=False,
                    text="",
                    error_type="runtime_error",
                    message=str(e),
                )
            )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ahura", description="Ahura CLI Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Start interactive chat mode")
    chat_parser.add_argument(
        "--session",
        default="new",
        help='Session mode: "new", "last", or "load:<session_id>"',
    )

    args = parser.parse_args(argv)

    if args.command == "chat":
        run_chat_loop(session_mode=args.session)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

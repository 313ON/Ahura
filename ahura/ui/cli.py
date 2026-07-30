from __future__ import annotations

import argparse
from typing import Optional

from ahura.commands.config_cmd import run_config_show
from ahura.commands.doctor import run_doctor
from ahura.commands.inspect_cmd import run_inspect


def run_chat(args: argparse.Namespace) -> int:
    from ahura.ui.chat import run_chat_mode
    return run_chat_mode()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ahura", description="Ahura CLI Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Start interactive chat mode")
    chat_parser.set_defaults(func=run_chat)

    doctor_parser = subparsers.add_parser("doctor", help="Run environment and runtime diagnostics")
    doctor_parser.set_defaults(func=lambda args: run_doctor())

    config_parser = subparsers.add_parser("config", help="Config operations")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)

    config_show_parser = config_subparsers.add_parser("show", help="Show effective configuration")
    config_show_parser.set_defaults(func=lambda args: run_config_show())

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a file or directory")
    inspect_parser.add_argument("path", help="Path to inspect")
    inspect_parser.add_argument("--head", type=int, default=20, help="Number of lines to show for files")
    inspect_parser.add_argument("--find", type=str, default=None, help="Search text inside a file")
    inspect_parser.set_defaults(func=lambda args: run_inspect(args.path, args.head, args.find))

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

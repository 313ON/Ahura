from __future__ import annotations

import os

from ahura.core.chat_service import ChatService
from ahura.core.provider import OpenRouterClient, ProviderError


def run_chat_mode() -> int:
    """Run Ahura interactive chat mode."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY is not set.")
        print("Run 'ahura doctor' for diagnostics.")
        return 1

    model = "openai/gpt-4.1-mini"

    client = OpenRouterClient(api_key=api_key, model=model)
    chat_service = ChatService(client=client)

    print("Ahura chat mode started. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("Ahura > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if user_input.lower() in {"exit", "quit"}:
            return 0

        if not user_input:
            continue

        try:
            reply = chat_service.ask(user_input)
        except ProviderError as exc:
            print(f"[provider-error] {exc}")
            continue
        except Exception as exc:
            print(f"[unexpected-error] {exc}")
            continue

        print()
        print(reply)
        print()

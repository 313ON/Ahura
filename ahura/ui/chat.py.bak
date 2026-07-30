from __future__ import annotations

import os

from ahura.core.chat_service import ChatService
from ahura.core.config import load_config
from ahura.core.provider import OpenRouterClient, ProviderError


def run_chat() -> int:
    """Run Ahura interactive chat mode."""
    cfg = load_config()

    api_key = os.getenv(cfg.api_key_name)
    if not api_key:
        print(f"{cfg.api_key_name} is not set.")
        return 1

    client = OpenRouterClient(
        api_key=api_key,
        model=cfg.model,
        max_tokens=cfg.max_tokens,
        temperature=cfg.temperature,
    )
    service = ChatService(client=client)

    print("Ahura chat mode started. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("Ahura > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() in {"exit", "quit"}:
            break

        if not user_input:
            continue

        try:
            response = service.ask(user_input)
            print()
            print(response)
            print()
        except ProviderError as exc:
            print(f"[provider-error] {exc}")

    return 0

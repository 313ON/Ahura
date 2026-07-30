from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ahura.core.config import load_config


def run_config_show() -> int:
    cfg = load_config()

    table = Table(title="Ahura Config")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("provider", cfg.provider)
    table.add_row("model", cfg.model)
    table.add_row("api_key_env", cfg.api_key_name)
    table.add_row("api_key_present", str(cfg.api_key_present))
    table.add_row("session_dir", str(cfg.session_dir))
    table.add_row("max_tokens", str(cfg.max_tokens))
    table.add_row("temperature", str(cfg.temperature))

    Console().print(table)
    return 0

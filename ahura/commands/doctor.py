from __future__ import annotations

import importlib
import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ahura.core.config import load_config


console = Console()


def _check_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, "ok"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _check_write_access(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(path)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def run_doctor() -> int:
    cfg = load_config()

    checks: list[tuple[str, bool, str]] = []

    checks.append((
        "Python executable",
        True,
        os.sys.executable,
    ))

    checks.append((
        "OPENROUTER_API_KEY",
        cfg.api_key_present,
        "set" if cfg.api_key_present else f"missing ({cfg.api_key_name})",
    ))

    ok_rich, msg_rich = _check_import("rich")
    checks.append(("Import: rich", ok_rich, msg_rich))

    ok_pkg, msg_pkg = _check_import("ahura")
    checks.append(("Import: ahura", ok_pkg, msg_pkg))

    ok_session, msg_session = _check_write_access(cfg.session_dir)
    checks.append(("Session dir writable", ok_session, msg_session))

    table = Table(title="Ahura Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="magenta")

    failures = 0
    for name, ok, details in checks:
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        if not ok:
            failures += 1
        table.add_row(name, status, details)

    console.print(table)
    return 0 if failures == 0 else 1

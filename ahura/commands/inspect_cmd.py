from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table


console = Console()


def _print_file_head(path: Path, head: int) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for idx, line in enumerate(lines[:head], start=1):
        console.print(f"[cyan]{idx:>4}[/cyan]  {line}")


def _search_in_file(path: Path, needle: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for idx, line in enumerate(lines, start=1):
        if needle.lower() in line.lower():
            matches.append((idx, line))
    return matches


def run_inspect(path_str: str, head: int = 20, find: str | None = None) -> int:
    path = Path(path_str).resolve()

    if not path.exists():
        console.print(f"[red]Path not found:[/red] {path}")
        return 1

    if path.is_dir():
        table = Table(title=f"Directory Listing: {path}")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Size", style="green")

        for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            kind = "DIR" if child.is_dir() else "FILE"
            size = "-" if child.is_dir() else str(child.stat().st_size)
            table.add_row(kind, child.name, size)

        console.print(table)
        return 0

    console.print(f"[bold]File:[/bold] {path}")
    console.print(f"[bold]Head ({head} lines):[/bold]")
    _print_file_head(path, head)

    if find:
        matches = _search_in_file(path, find)
        table = Table(title=f"Search Results: {find}")
        table.add_column("Line", style="cyan")
        table.add_column("Content", style="magenta")

        for line_no, content in matches[:200]:
            table.add_row(str(line_no), content)

        if matches:
            console.print(table)
        else:
            console.print(f"[yellow]No matches found[/yellow] for: {find}")

    return 0

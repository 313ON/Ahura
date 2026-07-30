from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ahura.response_types import AssistantResult


class AhuraRenderer:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def welcome(self) -> None:
        title = Text("AHURA", style="bold bright_cyan")
        title.append("  Ops Copilot", style="cyan")
        self.console.print(
            Panel(
                title,
                border_style="cyan",
                padding=(0, 2),
                subtitle="[dim]ForgeOS-family operations assistant[/dim]",
            )
        )

    def status(self, *, model: str, session_path: Path) -> None:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim cyan")
        table.add_column(style="white")
        table.add_row("Provider", "OpenRouter")
        table.add_row("Model", model)
        table.add_row("Session", str(session_path))
        self.console.print(Panel(table, title="STATUS", border_style="bright_black"))

    def help(self) -> None:
        table = Table(show_header=True, header_style="bold cyan", border_style="bright_black")
        table.add_column("Command", style="bright_cyan", no_wrap=True)
        table.add_column("Action")
        for command, action in (
            ("/help", "Show this command reference"),
            ("/models", "Show the active model policy"),
            ("/model set <model>", "Pin a preferred model"),
            ("/system [text]", "Show or update the system prompt"),
            ("/file <path>", "Attach a file summary"),
            ("/multiline", "Enter block input; finish with /end"),
            ("/reset", "Clear active context while preserving audit history"),
            ("/clear", "Clear the terminal"),
            ("/doctor", "Show session diagnostics"),
            ("/save", "Persist the current session"),
            ("/load <id>", "Load an existing session"),
            ("/exit", "Exit Ahura"),
        ):
            table.add_row(command, action)
        self.console.print(Panel(table, title="COMMANDS", border_style="cyan"))

    def assistant(self, result: AssistantResult) -> None:
        title = "ASSISTANT"
        if result.model:
            title = f"ASSISTANT · {result.model}"
        self.console.print(
            Panel(
                Markdown(result.text),
                title=title,
                title_align="left",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def error(self, result: AssistantResult) -> None:
        error_type = result.error_type or "runtime_error"
        message = result.message or "An unexpected error occurred."
        hint = self._hint(error_type, message)
        body = Text()
        body.append("Type     ", style="dim")
        body.append(f"{error_type}\n", style="bold bright_red")
        body.append("Message  ", style="dim")
        body.append(f"{message}\n", style="white")
        body.append("Hint     ", style="dim")
        body.append(hint, style="yellow")
        self.console.print(Panel(body, title="AHURA ERROR", border_style="red"))

    def command(self, message: str) -> None:
        self.console.print(Panel(message, border_style="bright_black", padding=(0, 1)))

    def info(self, message: str) -> None:
        self.console.print(f"[cyan]•[/cyan] {message}")

    def clear(self) -> None:
        self.console.clear()
        self.welcome()

    @staticmethod
    def _hint(error_type: str, message: str) -> str:
        lowered = message.casefold()
        if (
            "api key" in lowered
            or "openrouter_api_key" in lowered
            or "authorization" in lowered
            or "401" in lowered
        ):
            return "Check OPENROUTER_API_KEY and restart Ahura."
        if "rate limit" in lowered or "429" in lowered:
            return "Wait briefly or try a different model."
        if error_type in {"provider_error", "malformed_response", "empty_response"}:
            return "Try a different model; raw response is preserved for debugging."
        return "Run /doctor, verify connectivity, and retry."

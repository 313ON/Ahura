from io import StringIO

from rich.console import Console

from ahura.response_types import AssistantResult
from ahura.ui_render import AhuraRenderer


def make_renderer() -> tuple[AhuraRenderer, StringIO]:
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=100)
    return AhuraRenderer(console), output


def test_renders_assistant_markdown() -> None:
    renderer, output = make_renderer()

    renderer.assistant(AssistantResult(ok=True, text="## Result\n\n`ok`", model="demo"))

    rendered = output.getvalue()
    assert "ASSISTANT · demo" in rendered
    assert "Result" in rendered
    assert "ok" in rendered


def test_renders_structured_error() -> None:
    renderer, output = make_renderer()

    renderer.error(
        AssistantResult(
            ok=False,
            text="",
            error_type="provider_error",
            message="invalid API key",
        )
    )

    rendered = output.getvalue()
    assert "AHURA ERROR" in rendered
    assert "provider_error" in rendered
    assert "OPENROUTER_API_KEY" in rendered

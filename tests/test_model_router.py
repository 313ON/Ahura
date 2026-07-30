from ahura.model_router import AhuraModelRouter, ModelProfile
from ahura.response_types import AssistantResult


class FakeClient:
    def get_key_limits(self):
        raise AssertionError("Proactive checks are disabled in this test")

    def chat_completion(self, **_kwargs):
        return AssistantResult(ok=True, text="normalized response", raw="normalized response")


class FailingClient(FakeClient):
    def chat_completion(self, **_kwargs):
        return AssistantResult(
            ok=False,
            text="",
            error_type="malformed_response",
            message="bad payload",
            raw={"choices": ["bad"]},
        )


def test_route_chat_returns_assistant_result() -> None:
    router = AhuraModelRouter(
        FakeClient(),
        [ModelProfile(name="default", primary="demo-model", fallbacks=[])],
        proactive_limit_check=False,
    )

    result = router.route_chat([{"role": "user", "content": "hello"}])

    assert result.ok is True
    assert result.text == "normalized response"
    assert result.model == "demo-model"


def test_route_chat_returns_structured_failure() -> None:
    router = AhuraModelRouter(
        FailingClient(),
        [ModelProfile(name="default", primary="demo-model", fallbacks=[])],
        proactive_limit_check=False,
    )

    result = router.route_chat([{"role": "user", "content": "hello"}])

    assert result.ok is False
    assert result.error_type == "malformed_response"
    assert "bad payload" in (result.message or "")
    assert result.raw == {"choices": ["bad"]}

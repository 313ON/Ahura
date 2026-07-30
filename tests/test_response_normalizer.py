from ahura.response_normalizer import ResponseNormalizer


def test_normalizes_plain_string() -> None:
    result = ResponseNormalizer.normalize("hello", model="demo")

    assert result.ok is True
    assert result.text == "hello"
    assert result.model == "demo"
    assert result.raw == "hello"


def test_normalizes_provider_error_string() -> None:
    payload = {"error": "model unavailable"}

    result = ResponseNormalizer.normalize(payload)

    assert result.ok is False
    assert result.error_type == "provider_error"
    assert result.message == "model unavailable"
    assert result.raw is payload


def test_normalizes_provider_error_object() -> None:
    payload = {"error": {"message": "invalid key"}}

    result = ResponseNormalizer.normalize(payload)

    assert result.ok is False
    assert result.error_type == "provider_error"
    assert result.message == "invalid key"


def test_normalizes_chat_completion() -> None:
    payload = {
        "model": "openrouter/demo",
        "choices": [{"message": {"content": "response text"}, "finish_reason": "stop"}],
    }

    result = ResponseNormalizer.normalize(payload)

    assert result.ok is True
    assert result.text == "response text"
    assert result.model == "openrouter/demo"


def test_rejects_string_choice_without_raising() -> None:
    payload = {"choices": ["unexpected"]}

    result = ResponseNormalizer.normalize(payload)

    assert result.ok is False
    assert result.error_type == "malformed_response"


def test_rejects_missing_content() -> None:
    payload = {"choices": [{"message": {}}]}

    result = ResponseNormalizer.normalize(payload)

    assert result.ok is False
    assert result.error_type == "malformed_response"


def test_rejects_empty_payloads() -> None:
    for payload in (None, "", [], {}):
        result = ResponseNormalizer.normalize(payload)
        assert result.ok is False
        assert result.error_type == "empty_response"

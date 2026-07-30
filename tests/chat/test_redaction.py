from ahura.chat.redaction import redact_text


def test_redacts_openrouter_api_key_assignment() -> None:
    text = "OPENROUTER_API_KEY=secret-value-123"
    result = redact_text(text)
    assert "secret-value-123" not in result
    assert "***REDACTED***" in result


def test_redacts_sk_style_secret() -> None:
    text = "token: sk-abcDEF123_xyz"
    result = redact_text(text)
    assert "sk-abcDEF123_xyz" not in result
    assert "***REDACTED***" in result


def test_redacts_bearer_token() -> None:
    text = "Authorization: Bearer abc.def-ghi"
    result = redact_text(text)
    assert "abc.def-ghi" not in result
    assert "Bearer ***REDACTED***" in result

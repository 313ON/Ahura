from ahura.chat.multiline import read_block_input, read_multiline_input


def make_input(lines: list[str]):
    iterator = iter(lines)

    def _fake_input(_prompt: str = "") -> str:
        return next(iterator)

    return _fake_input


def test_read_multiline_input_backslash_continuation() -> None:
    # backslash continuation means: each continued line ends with "\"
    fake_input = make_input(["second line \\", "third line"])
    result = read_multiline_input("first line \\", input_func=fake_input)
    assert result == "first line\nsecond line\nthird line"


def test_read_block_input_until_end() -> None:
    fake_input = make_input(["line 1", "line 2", "/end"])
    result = read_block_input(input_func=fake_input)
    assert result == "line 1\nline 2"

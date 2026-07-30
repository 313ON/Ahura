from __future__ import annotations


def read_multiline_input(first_line: str, input_func=input) -> str:
    """
    Read continued input when a line ends with a trailing backslash.
    """
    parts: list[str] = []
    current = first_line

    while True:
        if current.endswith("\\"):
            parts.append(current[:-1].rstrip())
            current = input_func("... ")
            continue

        parts.append(current)
        break

    return "\n".join(parts)


def read_block_input(input_func=input, terminator: str = "/end") -> str:
    """
    Read explicit multiline block until terminator line is entered.
    """
    lines: list[str] = []
    while True:
        line = input_func("... ")
        if line.strip() == terminator:
            break
        lines.append(line)
    return "\n".join(lines)

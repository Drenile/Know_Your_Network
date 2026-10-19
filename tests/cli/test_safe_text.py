"""Tests that outside text can't control the terminal or inject Rich markup."""

import io

import pytest
from rich.console import Console

from kyn.cli.safe_text import safe_text


def rendered(text: str) -> str:
    buffer = io.StringIO()
    Console(file=buffer, color_system=None, width=200).print(safe_text(text))
    return buffer.getvalue().rstrip("\n")


def test_plain_text_is_unchanged() -> None:
    assert rendered("Living room TV") == "Living room TV"


@pytest.mark.parametrize(
    ("hostile", "shown"),
    [
        ("\x1b[2Jwiped", "?[2Jwiped"),  # Terminal code that clears the screen.
        ("\x1b]0;title\x07", "?]0;title?"),  # Changes the window title.
        ("abc‮dcba", "abc?dcba"),  # Right-to-left override.
        ("zero​width", "zero?width"),  # Invisible space.
        ("line\nbreak", "line?break"),  # Could fake extra rows.
    ],
)
def test_control_and_invisible_characters_are_replaced(
    hostile: str, shown: str
) -> None:
    assert rendered(hostile) == shown


@pytest.mark.parametrize("markup", ["[bold red]alert[/]", "[link=http://x]y[/link]"])
def test_rich_markup_is_shown_literally(markup: str) -> None:
    assert rendered(markup) == markup


def test_emoji_codes_are_shown_literally() -> None:
    assert rendered(":warning:") == ":warning:"

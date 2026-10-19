"""Make outside text safe to show in the terminal.

Text that comes from the network or the OS (device names, adapter names, makers) could
contain:
- Rich markup such as "[link=...]": avoided by building `Text` objects, which Rich
  never reads as markup.
- Terminal control codes such as ESC (\\x1b), which can recolour the screen, move the
  cursor or change the window title. Rich does not remove ESC, so we do.
- Invisible characters such as right-to-left overrides, which make text look different
  from what it is.
"""

from typing import Final

from rich.text import Text

REPLACEMENT: Final = "?"


def safe_text(text: str, style: str = "") -> Text:
    """Return `text` as plain Rich text, with every non-printable character replaced."""
    cleaned = "".join(char if char.isprintable() else REPLACEMENT for char in text)
    return Text(cleaned, style=style)

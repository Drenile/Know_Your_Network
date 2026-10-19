"""Smoke tests: prove the package installs, imports and runs."""

import pytest

import kyn
from kyn.__main__ import main


def test_version_is_set() -> None:
    assert kyn.__version__ == "0.0.1"


def test_no_command_prints_help_and_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([])

    assert exit_code == 0
    assert "scan" in capsys.readouterr().out


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert "Know Your Network 0.0.1" in capsys.readouterr().out


def test_unknown_command_is_refused() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["attack"])

    assert exit_info.value.code == 2

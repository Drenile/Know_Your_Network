"""Smoke tests: prove the package installs, imports and runs."""

import pytest

import kyn
from kyn.__main__ import main


def test_version_is_set() -> None:
    assert kyn.__version__ == "0.0.1"


def test_main_prints_name_and_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main()

    assert exit_code == 0
    assert "Know Your Network" in capsys.readouterr().out

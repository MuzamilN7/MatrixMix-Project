"""Tests for src/env.py (.env loading)."""
import os

import pytest

from src.env import load_env_key


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def write(tmp_path, text, encoding="utf-8"):
    f = tmp_path / ".env"
    f.write_bytes(text.encode(encoding))
    return f


def test_loads_key_from_env_file(tmp_path):
    assert load_env_key(path=write(tmp_path, "GROQ_API_KEY=abc123\n")) is True
    assert os.environ["GROQ_API_KEY"] == "abc123"


def test_real_environment_variable_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "from-env")
    load_env_key(path=write(tmp_path, "GROQ_API_KEY=from-file\n"))
    assert os.environ["GROQ_API_KEY"] == "from-env"


def test_quotes_spaces_and_other_lines_are_handled(tmp_path):
    f = write(tmp_path, "OTHER=1\n  GROQ_API_KEY = \"quoted-key\"  \nMORE=2\n")
    assert load_env_key(path=f) is True and os.environ["GROQ_API_KEY"] == "quoted-key"


def test_windows_bom_is_tolerated(tmp_path):
    assert load_env_key(path=write(tmp_path, "﻿GROQ_API_KEY=bom-key\r\n")) is True
    assert os.environ["GROQ_API_KEY"] == "bom-key"


@pytest.mark.parametrize("text", ["", "GROQ_API_KEY=\n", "GROQ_API_KEY\n", "OTHER_KEY=abc\n", "# GROQ_API_KEY=abc\n"])
def test_missing_or_empty_key_returns_false(tmp_path, text):
    assert load_env_key(path=write(tmp_path, text)) is False
    assert "GROQ_API_KEY" not in os.environ


def test_missing_file_returns_false(tmp_path):
    assert load_env_key(path=tmp_path / "nope.env") is False


def test_unreadable_encoding_returns_false_instead_of_crashing(tmp_path):
    # PowerShell's `echo ... > .env` writes UTF-16, which is not valid UTF-8.
    assert load_env_key(path=write(tmp_path, "GROQ_API_KEY=abc\n", encoding="utf-16")) is False

from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

import vault.cli as cli


class DummyDB:
    calls = []

    def add_memory(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id="test-id", type=kwargs.get("type", "thought"), tags=kwargs.get("tags", []))


def _setup_dummy_db(monkeypatch):
    DummyDB.calls = []
    monkeypatch.setattr(cli, "VaultDB", lambda: DummyDB())


def test_add_with_inline_content(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(cli.app, ["add", "hello world", "--type", "thought"])

    assert result.exit_code == 0
    assert len(DummyDB.calls) == 1
    assert DummyDB.calls[0]["content"] == "hello world"
    assert DummyDB.calls[0]["source"] == "cli"


def test_add_with_markdown_file(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("note.md").write_text("# note\ncontent", encoding="utf-8")
        result = runner.invoke(cli.app, ["add", "--file", "note.md"])

    assert result.exit_code == 0
    assert len(DummyDB.calls) == 1
    assert DummyDB.calls[0]["content"] == "# note\ncontent"
    assert DummyDB.calls[0]["source"] == "file"


def test_add_with_text_file(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("note.txt").write_text("plain text", encoding="utf-8")
        result = runner.invoke(cli.app, ["add", "--file", "note.txt"])

    assert result.exit_code == 0
    assert len(DummyDB.calls) == 1
    assert DummyDB.calls[0]["content"] == "plain text"
    assert DummyDB.calls[0]["source"] == "file"


def test_add_fails_when_file_missing(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli.app, ["add", "--file", "missing.md"])

    assert result.exit_code == 1
    assert "File not found or not a file" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_for_unsupported_extension(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("note.pdf").write_text("not supported", encoding="utf-8")
        result = runner.invoke(cli.app, ["add", "--file", "note.pdf"])

    assert result.exit_code == 1
    assert "Unsupported file type" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_for_non_utf8_file(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("bad.md").write_bytes(b"\xff\xfe\x00\x00")
        result = runner.invoke(cli.app, ["add", "--file", "bad.md"])

    assert result.exit_code == 1
    assert "Failed to read UTF-8 text from file" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_when_both_content_and_file(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("note.md").write_text("text", encoding="utf-8")
        result = runner.invoke(cli.app, ["add", "inline", "--file", "note.md"])

    assert result.exit_code == 1
    assert "Provide either inline content or --file, not both" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_when_neither_content_nor_file(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(cli.app, ["add"])

    assert result.exit_code == 1
    assert "Provide content or --file PATH" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_when_content_is_whitespace(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(cli.app, ["add", "   "])

    assert result.exit_code == 1
    assert "Provide content or --file PATH" in result.output
    assert len(DummyDB.calls) == 0


def test_add_fails_when_file_is_empty(monkeypatch):
    _setup_dummy_db(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("empty.md").write_text("\n\n", encoding="utf-8")
        result = runner.invoke(cli.app, ["add", "--file", "empty.md"])

    assert result.exit_code == 1
    assert "File is empty" in result.output
    assert len(DummyDB.calls) == 0

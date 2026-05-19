from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.main import app

runner: CliRunner = CliRunner()


def test_list_root_filesystem(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    files: list[str] = backend.list_files_in_vault()
    assert "note.md" in files
    assert "notes/" in files


def test_read_file(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    payload = backend.read_file("note.md")
    assert payload.encoding == "utf-8"
    assert "Hello world" in payload.content.decode("utf-8")


def test_write_binary_round_trip(tmp_vault: Path) -> None:
    from obsidian_cli.models import FilePayload

    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    data: bytes = b"\x89PNG\r\n\x1a\n"
    backend.write_file(
        "assets/test.png",
        FilePayload.from_bytes("assets/test.png", data, content_type="image/png"),
    )
    read_back = backend.read_file("assets/test.png")
    assert read_back.is_binary
    assert read_back.content == data


def test_cli_file_read(tmp_vault: Path) -> None:
    result = runner.invoke(app, ["--vault", str(tmp_vault), "file", "read", "note.md"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "Hello world" in data["content"]


def test_cli_list_root(tmp_vault: Path) -> None:
    result = runner.invoke(app, ["--vault", str(tmp_vault), "list-root"])
    assert result.exit_code == 0
    assert "note.md" in result.stdout


def test_legacy_read_alias(tmp_vault: Path) -> None:
    result = runner.invoke(app, ["--vault", str(tmp_vault), "read", "note.md"])
    assert result.exit_code == 0

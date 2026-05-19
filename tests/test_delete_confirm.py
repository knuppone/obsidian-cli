from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.main import app

runner: CliRunner = CliRunner()


def test_delete_requires_confirm(tmp_vault: Path) -> None:
    result = runner.invoke(
        app,
        ["--vault", str(tmp_vault), "delete", "note.md"],
    )
    assert result.exit_code == 1


def test_delete_file(tmp_vault: Path) -> None:
    target: Path = tmp_vault / "note.md"
    assert target.exists()
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    backend.delete_file("note.md")
    assert not target.exists()


def test_cli_delete_with_confirm(tmp_vault: Path) -> None:
    result = runner.invoke(
        app,
        ["--vault", str(tmp_vault), "delete", "note.md", "--confirm"],
    )
    assert result.exit_code == 0
    assert not (tmp_vault / "note.md").exists()

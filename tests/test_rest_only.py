from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from obsidian_cli.errors import RestOnlyError
from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.main import app

runner: CliRunner = CliRunner()


def test_fs_search_json_raises(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    with pytest.raises(RestOnlyError):
        backend.search_json({"glob": ["*.md", {"var": "path"}]})


def test_cli_active_requires_rest(tmp_vault: Path) -> None:
    result = runner.invoke(
        app,
        ["--vault", str(tmp_vault), "--backend", "fs", "active", "read"],
    )
    assert result.exit_code == 1
    assert "rest" in result.stderr.lower() or "REST" in result.stderr

from __future__ import annotations

from pathlib import Path

from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.search_fs import simple_search
from obsidian_cli.search_tag_fs import search_by_tag


def test_simple_search_finds_match(tmp_vault: Path) -> None:
    results: list[dict] = simple_search(tmp_vault, "project")
    filenames: list[str] = [item["filename"] for item in results]
    assert "notes/meeting.md" in filenames


def test_search_tag_fs(tmp_vault: Path) -> None:
    paths: list[str] = search_by_tag(tmp_vault, "work")
    assert "notes/nested.md" in paths


def test_backend_search_text(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    results: list[dict] = backend.search_text("Hello", context_length=20)
    assert any(item["filename"] == "note.md" for item in results)

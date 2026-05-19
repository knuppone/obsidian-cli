from __future__ import annotations

from pathlib import Path

from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.models import PatchTarget
from obsidian_cli.patch.headings import find_heading_paths, patch_heading

SAMPLE: str = """# Outer

Intro

## Inner

Body ^block1
"""


def test_find_heading_paths_bare_name() -> None:
    paths: list[str] = find_heading_paths(SAMPLE, "Inner")
    assert paths == ["Outer::Inner"]


def test_filesystem_patch_heading(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    backend.patch_file(
        "notes/nested.md",
        PatchTarget("append", "heading", "Inner", "Added line\n"),
    )
    payload = backend.read_file("notes/nested.md")
    assert isinstance(payload.content, bytes)
    assert "Added line" in payload.content.decode("utf-8")

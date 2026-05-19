from __future__ import annotations

from pathlib import Path

from obsidian_cli.backends.filesystem import FilesystemBackend
from obsidian_cli.models import PatchTarget
from obsidian_cli.patch.frontmatter import patch_frontmatter, split_frontmatter


def test_split_frontmatter() -> None:
    content: str = "---\ntitle: Note\n---\n\nBody\n"
    data, body, had_fm = split_frontmatter(content)
    assert had_fm is True
    assert data["title"] == "Note"
    assert "Body" in body


def test_filesystem_patch_frontmatter(tmp_vault: Path) -> None:
    backend: FilesystemBackend = FilesystemBackend(tmp_vault)
    backend.patch_file(
        "notes/nested.md",
        PatchTarget("replace", "frontmatter", "tags", "[work, urgent]"),
    )
    text: str = backend.get_file_contents("notes/nested.md")
    assert "urgent" in text

from __future__ import annotations

from obsidian_cli.patch.blocks import patch_block


def test_patch_block_append() -> None:
    content: str = "Line one\nLine two ^myblock\n"
    updated: str = patch_block(content, "append", "myblock", "Line three\n")
    assert "Line three" in updated
    assert "^myblock" in updated


def test_patch_block_replace() -> None:
    content: str = "Before\nTarget ^id1\nAfter\n"
    updated: str = patch_block(content, "replace", "id1", "New block\n")
    assert "New block" in updated
    assert "Target" not in updated

from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_cli.paths import PathEscapeError, normalize_vault_relative, resolve_in_vault


def test_normalize_strips_leading_slash() -> None:
    assert normalize_vault_relative("/notes/foo.md") == "notes/foo.md"


def test_normalize_rejects_parent_segments() -> None:
    with pytest.raises(PathEscapeError):
        normalize_vault_relative("../secret")


def test_resolve_in_vault(tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    vault.mkdir()
    resolved: Path = resolve_in_vault(vault, "notes/a.md")
    assert resolved == (vault / "notes" / "a.md").resolve()


def test_resolve_rejects_escape(tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    vault.mkdir()
    outside: Path = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    link: Path = vault / "link"
    link.symlink_to(outside)
    with pytest.raises(PathEscapeError):
        resolve_in_vault(vault, "link")

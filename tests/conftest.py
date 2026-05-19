from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    vault: Path = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    (vault / "note.md").write_text("# Root\n\nHello world.\n", encoding="utf-8")
    (vault / "notes").mkdir()
    (vault / "notes" / "meeting.md").write_text(
        "# Meeting\n\nDiscuss the project.\n",
        encoding="utf-8",
    )
    (vault / "notes" / "nested.md").write_text(
        "---\ntags:\n  - work\n---\n\n# Outer\n\n## Inner\n\nBlock line ^abc123\n",
        encoding="utf-8",
    )
    return vault

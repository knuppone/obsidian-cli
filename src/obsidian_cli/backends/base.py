from __future__ import annotations

from typing import Any, Literal, Optional, Protocol

from obsidian_cli.models import FilePayload, NoteMetadata, PatchTarget

Operation = Literal["append", "prepend", "replace"]
TargetType = Literal["heading", "block", "frontmatter"]


class VaultBackend(Protocol):
    def list_files_in_vault(self) -> list[str]:
        ...

    def list_files_in_dir(self, dirpath: str) -> list[str]:
        ...

    def read_file(self, filepath: str, *, metadata: bool = False) -> FilePayload | NoteMetadata:
        ...

    def write_file(self, filepath: str, payload: FilePayload) -> None:
        ...

    def append_file(self, filepath: str, content: str) -> None:
        ...

    def patch_file(self, filepath: str, patch: PatchTarget) -> None:
        ...

    def delete_file(self, filepath: str) -> None:
        ...

    def get_frontmatter(self, filepath: str) -> dict[str, Any]:
        ...

    def search_text(self, query: str, context_length: int = 100) -> list[dict[str, Any]]:
        ...

    def search_tag(self, tag: str, dirpath: Optional[str] = None) -> list[str]:
        ...

    def search_json(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        ...

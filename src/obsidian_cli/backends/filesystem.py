from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from obsidian_cli.backends.base import Operation, TargetType
from obsidian_cli.errors import RestOnlyError
from obsidian_cli.models import DEFAULT_TEXT_CONTENT_TYPE, FilePayload, NoteMetadata, PatchTarget
from obsidian_cli.patch import (
    find_heading_paths,
    patch_block,
    patch_frontmatter,
    patch_heading,
)
from obsidian_cli.patch.frontmatter import split_frontmatter
from obsidian_cli.paths import normalize_vault_relative, resolve_in_vault, should_skip_dir
from obsidian_cli.search_fs import simple_search
from obsidian_cli.search_tag_fs import search_by_tag

_BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".pdf",
        ".zip",
        ".mp3",
        ".mp4",
        ".wav",
        ".ico",
        ".heic",
    }
)


def _guess_binary(path: Path) -> bool:
    if path.suffix.lower() in _BINARY_EXTENSIONS:
        return True
    try:
        path.read_text(encoding="utf-8")
        return False
    except UnicodeDecodeError:
        return True


class FilesystemBackend:
    def __init__(self, vault_root: Path) -> None:
        self._vault_root: Path = vault_root.resolve()

    def list_files_in_vault(self) -> List[str]:
        return self._list_directory("")

    def list_files_in_dir(self, dirpath: str) -> List[str]:
        return self._list_directory(dirpath)

    def _list_directory(self, dirpath: str) -> List[str]:
        target: Path = (
            self._vault_root
            if not dirpath
            else resolve_in_vault(self._vault_root, dirpath)
        )
        if not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {dirpath!r}")

        entries: List[str] = []
        for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            name: str = child.name
            if should_skip_dir(name):
                continue
            if name.startswith("."):
                continue
            suffix: str = "/" if child.is_dir() else ""
            entries.append(name + suffix)
        return entries

    def read_file(
        self, filepath: str, *, metadata: bool = False
    ) -> Union[FilePayload, NoteMetadata]:
        path: Path = resolve_in_vault(self._vault_root, filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath!r}")

        is_binary: bool = _guess_binary(path)
        content_type: Optional[str] = mimetypes.guess_type(path.name)[0]
        if metadata and not is_binary:
            text: str = path.read_text(encoding="utf-8")
            frontmatter, body, _ = split_frontmatter(text)
            tags: List[str] = []
            raw_tags: object = frontmatter.get("tags")
            if isinstance(raw_tags, str):
                tags = [raw_tags]
            elif isinstance(raw_tags, list):
                tags = [str(item) for item in raw_tags]
            return NoteMetadata(
                path=filepath,
                frontmatter=frontmatter,
                content=body if body else text,
                tags=tags,
            )

        if is_binary:
            return FilePayload.from_bytes(
                filepath,
                path.read_bytes(),
                is_binary=True,
                content_type=content_type,
            )
        return FilePayload.from_text(
            filepath,
            path.read_text(encoding="utf-8"),
            content_type=content_type or DEFAULT_TEXT_CONTENT_TYPE,
        )

    def write_file(self, filepath: str, payload: FilePayload) -> None:
        path: Path = resolve_in_vault(self._vault_root, payload.path or filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload.content)

    def append_file(self, filepath: str, content: str) -> None:
        path: Path = resolve_in_vault(self._vault_root, filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            if _guess_binary(path):
                raise ValueError(f"Cannot append text to binary file: {filepath!r}")
            existing: str = path.read_text(encoding="utf-8")
            if existing and not existing.endswith("\n"):
                content = "\n" + content
            with path.open("a", encoding="utf-8") as handle:
                handle.write(content)
        else:
            path.write_text(content, encoding="utf-8")

    def patch_file(self, filepath: str, patch: PatchTarget) -> None:
        if _guess_binary(resolve_in_vault(self._vault_root, filepath)):
            raise ValueError(f"Cannot patch binary file: {filepath!r}")
        self.patch_content(
            filepath,
            patch.operation,  # type: ignore[arg-type]
            patch.target_type,  # type: ignore[arg-type]
            patch.target,
            patch.content,
        )

    def patch_content(
        self,
        filepath: str,
        operation: Operation,
        target_type: TargetType,
        target: str,
        content: str,
    ) -> None:
        path: Path = resolve_in_vault(self._vault_root, filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath!r}")

        file_content: str = path.read_text(encoding="utf-8")
        updated: str

        if target_type == "heading":
            qualified: str = target
            if "::" not in target:
                candidates: List[str] = find_heading_paths(file_content, target)
                if len(candidates) == 1:
                    qualified = candidates[0]
                elif len(candidates) > 1:
                    joined: str = ", ".join(candidates)
                    raise ValueError(
                        f"Ambiguous heading {target!r}. Candidates: {joined}. "
                        "Use :: delimiter for fully qualified paths."
                    )
            updated = patch_heading(file_content, operation, qualified, content)
        elif target_type == "block":
            block_id: str = target.lstrip("^")
            updated = patch_block(file_content, operation, block_id, content)
        elif target_type == "frontmatter":
            updated = patch_frontmatter(file_content, operation, target, content)
        else:
            raise ValueError(f"Unsupported target_type: {target_type!r}")

        path.write_text(updated, encoding="utf-8")

    def delete_file(self, filepath: str) -> None:
        normalized: str = normalize_vault_relative(filepath)
        path: Path = resolve_in_vault(self._vault_root, normalized)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {filepath!r}")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def get_frontmatter(self, filepath: str) -> Dict[str, Any]:
        result = self.read_file(filepath, metadata=True)
        if isinstance(result, NoteMetadata):
            return dict(result.frontmatter)
        raise ValueError(f"Cannot read frontmatter for binary file: {filepath!r}")

    def search_text(self, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
        return simple_search(self._vault_root, query, context_length)

    def search_tag(self, tag: str, dirpath: Optional[str] = None) -> List[str]:
        return search_by_tag(self._vault_root, tag, dirpath)

    def search_json(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise RestOnlyError("JsonLogic search")

    def get_file_contents(self, filepath: str) -> str:
        payload = self.read_file(filepath)
        if isinstance(payload, NoteMetadata):
            return payload.content
        if payload.is_binary:
            raise ValueError(f"File is binary: {filepath!r}")
        return payload.content.decode("utf-8")

    def append_content(self, filepath: str, content: str) -> None:
        self.append_file(filepath, content)

    def search(self, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
        return self.search_text(query, context_length)

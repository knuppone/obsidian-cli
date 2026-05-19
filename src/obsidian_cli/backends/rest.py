from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from obsidian_cli.backends.base import Operation, TargetType
from obsidian_cli.backends.rest_client import RestHttpClient
from obsidian_cli.config import AppConfig
from obsidian_cli.errors import RestOnlyError
from obsidian_cli.models import (
    DEFAULT_TEXT_CONTENT_TYPE,
    FilePayload,
    NoteMetadata,
    PatchTarget,
    Period,
    VALID_PERIODS,
)
from obsidian_cli.patch.headings import find_heading_paths


class RestApiBackend:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = RestHttpClient(config)

    def list_files_in_vault(self) -> List[str]:
        response = self._client.request("GET", "/vault/")
        return list(response.json()["files"])

    def list_files_in_dir(self, dirpath: str) -> List[str]:
        response = self._client.request("GET", f"/vault/{dirpath}/")
        return list(response.json()["files"])

    def read_file(
        self, filepath: str, *, metadata: bool = False
    ) -> Union[FilePayload, NoteMetadata]:
        accept: Optional[str] = (
            RestHttpClient.note_json_accept() if metadata else "application/json"
        )
        response = self._client.request("GET", f"/vault/{filepath}", accept=accept)
        if metadata:
            payload: Dict[str, Any] = response.json()
            frontmatter: Dict[str, Any] = dict(payload.get("frontmatter") or {})
            tags_raw: object = frontmatter.get("tags", [])
            tags: List[str] = []
            if isinstance(tags_raw, str):
                tags = [tags_raw]
            elif isinstance(tags_raw, list):
                tags = [str(item) for item in tags_raw]
            return NoteMetadata(
                path=filepath,
                frontmatter=frontmatter,
                content=str(payload.get("content", "")),
                tags=tags,
            )
        content_type: Optional[str] = response.headers.get("Content-Type")
        raw: bytes = response.content
        is_binary: bool = not _looks_like_text(raw, content_type)
        return FilePayload(
            path=filepath,
            content=raw,
            is_binary=is_binary,
            content_type=content_type,
        )

    def write_file(self, filepath: str, payload: FilePayload) -> None:
        content_type: str = payload.content_type or (
            DEFAULT_TEXT_CONTENT_TYPE if not payload.is_binary else "application/octet-stream"
        )
        self._client.request(
            "PUT",
            f"/vault/{filepath}",
            data=payload.content,
            content_type=content_type,
            accept=None,
        )

    def append_file(self, filepath: str, content: str) -> None:
        self._client.request(
            "POST",
            f"/vault/{filepath}",
            data=content.encode("utf-8"),
            content_type=RestHttpClient.text_content_type(),
            accept=None,
        )

    def patch_file(self, filepath: str, patch: PatchTarget) -> None:
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
        try:
            self._patch_content_raw(filepath, operation, target_type, target, content)
        except Exception as exc:
            if (
                target_type != "heading"
                or "::" in target
                or "Error 40080" not in str(exc)
            ):
                raise
            file_content: str = self.get_file_contents(filepath)
            candidates: List[str] = find_heading_paths(file_content, target)
            if len(candidates) == 1:
                self._patch_content_raw(
                    filepath, operation, target_type, candidates[0], content
                )
                return
            if len(candidates) > 1:
                joined: str = ", ".join(candidates)
                raise RuntimeError(
                    f"Ambiguous heading {target!r}. Candidates: {joined}. "
                    "Specify the qualified path with '::' delimiter."
                ) from exc
            raise

    def _patch_content_raw(
        self,
        filepath: str,
        operation: Operation,
        target_type: TargetType,
        target: str,
        content: str,
    ) -> None:
        self._client.patch_with_target(
            f"/vault/{filepath}",
            content,
            operation,
            target_type,
            target,
        )

    def delete_file(self, filepath: str) -> None:
        self._client.request("DELETE", f"/vault/{filepath}", accept=None)

    def get_frontmatter(self, filepath: str) -> Dict[str, Any]:
        meta = self.read_file(filepath, metadata=True)
        if isinstance(meta, NoteMetadata):
            return dict(meta.frontmatter)
        raise ValueError(f"Cannot read frontmatter for binary file: {filepath!r}")

    def search_text(self, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
        response = self._client.request(
            "POST",
            "/search/simple/",
            params=dict(query=query, contextLength=context_length),
        )
        payload: Any = response.json()
        if isinstance(payload, list):
            return payload
        return list(payload)

    def search_json(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        response = self._client.request(
            "POST",
            "/search/",
            json_body=query,
            content_type=RestHttpClient.jsonlogic_content_type(),
        )
        payload: Any = response.json()
        if isinstance(payload, list):
            return payload
        return list(payload)

    def search_tag(self, tag: str, dirpath: Optional[str] = None) -> List[str]:
        normalized: str = tag.lstrip("#")
        tag_query: Dict[str, Any] = {"in": [normalized, {"var": "tags"}]}
        if dirpath:
            prefix: str = dirpath.rstrip("/") + "/"
            query: Dict[str, Any] = {
                "and": [
                    tag_query,
                    {"glob": [f"{prefix}*", {"var": "path"}]},
                ]
            }
        else:
            query = tag_query
        results: List[Dict[str, Any]] = self.search_json(query)
        return [str(item["filename"]) for item in results if "filename" in item]

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

    def active_read(self, *, metadata: bool = False) -> Union[FilePayload, NoteMetadata]:
        accept: Optional[str] = (
            RestHttpClient.note_json_accept() if metadata else "application/json"
        )
        response = self._client.request("GET", "/active/", accept=accept)
        if metadata:
            payload: Dict[str, Any] = response.json()
            frontmatter: Dict[str, Any] = dict(payload.get("frontmatter") or {})
            return NoteMetadata(
                path="active",
                frontmatter=frontmatter,
                content=str(payload.get("content", "")),
                tags=[],
            )
        content_type: Optional[str] = response.headers.get("Content-Type")
        raw: bytes = response.content
        return FilePayload(
            path="active",
            content=raw,
            is_binary=not _looks_like_text(raw, content_type),
            content_type=content_type,
        )

    def active_write(self, payload: FilePayload) -> None:
        content_type: str = payload.content_type or DEFAULT_TEXT_CONTENT_TYPE
        self._client.request(
            "PUT",
            "/active/",
            data=payload.content,
            content_type=content_type,
            accept=None,
        )

    def active_append(self, content: str) -> None:
        self._client.request(
            "POST",
            "/active/",
            data=content.encode("utf-8"),
            content_type=RestHttpClient.text_content_type(),
            accept=None,
        )

    def active_patch(self, patch: PatchTarget) -> None:
        self._client.patch_with_target(
            "/active/",
            patch.content,
            patch.operation,
            patch.target_type,
            patch.target,
            target_scope=patch.target_scope,
        )

    def active_delete(self) -> None:
        self._client.request("DELETE", "/active/", accept=None)

    def periodic_get(
        self, period: Period, *, metadata: bool = False
    ) -> Union[FilePayload, NoteMetadata]:
        _validate_period(period)
        accept: Optional[str] = (
            RestHttpClient.note_json_accept() if metadata else "text/markdown"
        )
        response = self._client.request("GET", f"/periodic/{period}/", accept=accept)
        if metadata:
            payload: Dict[str, Any] = response.json()
            return NoteMetadata(
                path=f"periodic/{period}",
                frontmatter=dict(payload.get("frontmatter") or {}),
                content=str(payload.get("content", "")),
                tags=[],
            )
        return FilePayload.from_text(
            f"periodic/{period}",
            response.text,
        )

    def periodic_recent(
        self,
        period: Period,
        limit: int = 5,
        include_content: bool = False,
    ) -> List[Dict[str, Any]]:
        _validate_period(period)
        response = self._client.request(
            "GET",
            f"/periodic/{period}/recent",
            params=dict(limit=limit, includeContent=include_content),
        )
        payload: Any = response.json()
        if isinstance(payload, list):
            return payload
        return list(payload)

    def periodic_write(self, period: Period, payload: FilePayload) -> None:
        _validate_period(period)
        content_type: str = payload.content_type or DEFAULT_TEXT_CONTENT_TYPE
        self._client.request(
            "PUT",
            f"/periodic/{period}/",
            data=payload.content,
            content_type=content_type,
            accept=None,
        )

    def periodic_append(self, period: Period, content: str) -> None:
        _validate_period(period)
        self._client.request(
            "POST",
            f"/periodic/{period}/",
            data=content.encode("utf-8"),
            content_type=RestHttpClient.text_content_type(),
            accept=None,
        )

    def periodic_patch(self, period: Period, patch: PatchTarget) -> None:
        _validate_period(period)
        self._client.patch_with_target(
            f"/periodic/{period}/",
            patch.content,
            patch.operation,
            patch.target_type,
            patch.target,
            target_scope=patch.target_scope,
        )

    def periodic_delete(self, period: Period) -> None:
        _validate_period(period)
        self._client.request("DELETE", f"/periodic/{period}/", accept=None)

    def list_commands(self) -> List[Dict[str, Any]]:
        response = self._client.request("GET", "/commands/")
        payload: Dict[str, Any] = response.json()
        commands: object = payload.get("commands", [])
        if isinstance(commands, list):
            return list(commands)
        return []

    def run_command(self, command_id: str) -> None:
        self._client.request("POST", f"/commands/{command_id}/", accept=None)


def _validate_period(period: str) -> None:
    if period not in VALID_PERIODS:
        raise ValueError(
            f"Invalid period {period!r}. Must be one of: {', '.join(VALID_PERIODS)}"
        )


def _looks_like_text(raw: bytes, content_type: Optional[str]) -> bool:
    if content_type and content_type.startswith("text/"):
        return True
    if content_type and "markdown" in content_type:
        return True
    if not raw:
        return True
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

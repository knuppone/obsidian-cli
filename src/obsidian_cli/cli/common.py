from __future__ import annotations

import base64
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import typer

from obsidian_cli.backends import FilesystemBackend, RestApiBackend, VaultBackend
from obsidian_cli.backends.base import Operation, TargetType
from obsidian_cli.config import AppConfig, BackendKind
from obsidian_cli.errors import RestOnlyError
from obsidian_cli.models import FilePayload, NoteMetadata, PatchTarget
from obsidian_cli.output import emit_error, emit_json


class BackendOption(str, Enum):
    fs = "fs"
    rest = "rest"


class OperationOption(str, Enum):
    append = "append"
    prepend = "prepend"
    replace = "replace"


class TargetTypeOption(str, Enum):
    heading = "heading"
    block = "block"
    frontmatter = "frontmatter"


class PeriodOption(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


def get_backend(config: AppConfig) -> VaultBackend:
    if config.backend == BackendKind.REST:
        return RestApiBackend(config)
    return FilesystemBackend(config.vault_root)


def get_rest_backend(config: AppConfig) -> RestApiBackend:
    if config.backend != BackendKind.REST:
        raise RestOnlyError("this operation")
    return RestApiBackend(config)


def config_from_ctx(ctx: typer.Context) -> AppConfig:
    obj: Any = ctx.obj
    if not obj or "config" not in obj:
        emit_error("CLI context not initialized.")
        raise typer.Exit(code=1)
    return obj["config"]


def read_content_option(content: Optional[str]) -> str:
    if content is not None:
        return content
    return sys.stdin.read()


def read_bytes_option(
    content: Optional[str],
    *,
    base64_input: bool,
) -> bytes:
    if base64_input:
        raw: str = read_content_option(content)
        return base64.b64decode(raw.strip())
    text: str = read_content_option(content)
    return text.encode("utf-8")


def build_file_payload(
    filepath: str,
    data: bytes,
    *,
    base64_input: bool,
    content_type: Optional[str],
) -> FilePayload:
    is_binary: bool = base64_input
    if not is_binary:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            is_binary = True
    return FilePayload(
        path=filepath,
        content=data,
        is_binary=is_binary,
        content_type=content_type,
    )


def emit_file_or_metadata(result: Union[FilePayload, NoteMetadata]) -> None:
    if isinstance(result, NoteMetadata):
        emit_json(result.to_json_dict())
        return
    emit_json(result.to_json_dict())


def patch_target_from_options(
    operation: OperationOption,
    target_type: TargetTypeOption,
    target: str,
    content: str,
) -> PatchTarget:
    return PatchTarget(
        operation=operation.value,
        target_type=target_type.value,
        target=target,
        content=content,
    )


def load_json_query(query_file: Optional[Path], tag: Optional[str], dirpath: Optional[str]) -> dict[str, Any]:
    if query_file is not None:
        return json.loads(query_file.read_text(encoding="utf-8"))
    if tag:
        normalized: str = tag.lstrip("#")
        tag_query: dict[str, Any] = {"in": [normalized, {"var": "tags"}]}
        if dirpath:
            prefix: str = dirpath.rstrip("/") + "/"
            return {
                "and": [
                    tag_query,
                    {"glob": [f"{prefix}*", {"var": "path"}]},
                ]
            }
        return tag_query
    raw: str = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Provide a query file, --tag, or JSON on stdin.")
    return json.loads(raw)

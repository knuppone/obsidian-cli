from __future__ import annotations

from typing import Optional

import typer

from obsidian_cli.cli.common import (
    OperationOption,
    TargetTypeOption,
    build_file_payload,
    config_from_ctx,
    emit_file_or_metadata,
    get_backend,
    patch_target_from_options,
    read_bytes_option,
    read_content_option,
)
from obsidian_cli.help_text import (
    FILE_APPEND_DOC,
    FILE_DELETE_DOC,
    FILE_GROUP_HELP,
    FILE_PATCH_DOC,
    FILE_READ_DOC,
    FILE_WRITE_DOC,
)
from obsidian_cli.output import emit_error, emit_json

file_app = typer.Typer(help=FILE_GROUP_HELP)


@file_app.command("read")
def file_read(
    ctx: typer.Context,
    filepath: str = typer.Argument(..., help="Path relative to vault root."),
    metadata: bool = typer.Option(False, "--metadata", help="Return parsed note metadata."),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    try:
        result = backend.read_file(filepath, metadata=metadata)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_file_or_metadata(result)


file_read.__doc__ = FILE_READ_DOC


@file_app.command("write")
def file_write(
    ctx: typer.Context,
    filepath: str = typer.Argument(..., help="Path relative to vault root."),
    content: Optional[str] = typer.Option(None, "--content", help="Body; stdin if omitted."),
    content_type: Optional[str] = typer.Option(None, "--content-type"),
    base64_input: bool = typer.Option(False, "--base64", help="Decode stdin/--content as base64."),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    data = read_bytes_option(content, base64_input=base64_input)
    payload = build_file_payload(filepath, data, base64_input=base64_input, content_type=content_type)
    try:
        backend.write_file(filepath, payload)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully wrote {filepath}"))


file_write.__doc__ = FILE_WRITE_DOC


@file_app.command("append")
def file_append(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    try:
        backend.append_file(filepath, read_content_option(content))
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully appended content to {filepath}"))


file_append.__doc__ = FILE_APPEND_DOC


@file_app.command("patch")
def file_patch(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    operation: OperationOption = typer.Option(..., "--operation"),
    target_type: TargetTypeOption = typer.Option(..., "--target-type"),
    target: str = typer.Option(..., "--target"),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    patch = patch_target_from_options(
        operation, target_type, target, read_content_option(content)
    )
    try:
        backend.patch_file(filepath, patch)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully patched content in {filepath}"))


file_patch.__doc__ = FILE_PATCH_DOC


@file_app.command("delete")
def file_delete(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    if not confirm:
        emit_error("Pass --confirm to delete.")
        raise typer.Exit(code=1)
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    try:
        backend.delete_file(filepath)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully deleted {filepath}"))


file_delete.__doc__ = FILE_DELETE_DOC

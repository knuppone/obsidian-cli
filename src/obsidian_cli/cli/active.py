from __future__ import annotations

from typing import Optional

import typer

from obsidian_cli.backends.rest import RestApiBackend
from obsidian_cli.cli.common import (
    OperationOption,
    TargetTypeOption,
    build_file_payload,
    config_from_ctx,
    emit_file_or_metadata,
    get_rest_backend,
    patch_target_from_options,
    read_bytes_option,
    read_content_option,
)
from obsidian_cli.config import AppConfig
from obsidian_cli.output import emit_error, emit_json

active_app = typer.Typer(help="Read or write the file open in Obsidian (REST only).")


def _rest(ctx: typer.Context) -> RestApiBackend:
    config: AppConfig = config_from_ctx(ctx)
    try:
        return get_rest_backend(config)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc


@active_app.command("read")
def active_read(
    ctx: typer.Context,
    metadata: bool = typer.Option(False, "--metadata"),
) -> None:
    rest = _rest(ctx)
    try:
        result = rest.active_read(metadata=metadata)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_file_or_metadata(result)


@active_app.command("write")
def active_write(
    ctx: typer.Context,
    content: Optional[str] = typer.Option(None, "--content"),
    content_type: Optional[str] = typer.Option(None, "--content-type"),
    base64_input: bool = typer.Option(False, "--base64"),
) -> None:
    rest = _rest(ctx)
    data = read_bytes_option(content, base64_input=base64_input)
    payload = build_file_payload("active", data, base64_input=base64_input, content_type=content_type)
    try:
        rest.active_write(payload)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message="Successfully wrote active file"))


@active_app.command("append")
def active_append(
    ctx: typer.Context,
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    rest = _rest(ctx)
    try:
        rest.active_append(read_content_option(content))
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message="Successfully appended to active file"))


@active_app.command("patch")
def active_patch(
    ctx: typer.Context,
    operation: OperationOption = typer.Option(..., "--operation"),
    target_type: TargetTypeOption = typer.Option(..., "--target-type"),
    target: str = typer.Option(..., "--target"),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    rest = _rest(ctx)
    patch = patch_target_from_options(
        operation, target_type, target, read_content_option(content)
    )
    try:
        rest.active_patch(patch)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message="Successfully patched active file"))


@active_app.command("delete")
def active_delete(ctx: typer.Context) -> None:
    rest = _rest(ctx)
    try:
        rest.active_delete()
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message="Successfully deleted active file"))

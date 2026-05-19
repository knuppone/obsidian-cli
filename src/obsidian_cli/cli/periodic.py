from __future__ import annotations

from typing import Optional

import typer

from obsidian_cli.cli.common import (
    OperationOption,
    PeriodOption,
    TargetTypeOption,
    build_file_payload,
    config_from_ctx,
    emit_file_or_metadata,
    get_rest_backend,
    patch_target_from_options,
    read_bytes_option,
    read_content_option,
)
from obsidian_cli.models import Period
from obsidian_cli.backends.rest import RestApiBackend
from obsidian_cli.config import AppConfig
from obsidian_cli.output import emit_error, emit_json

periodic_app = typer.Typer(help="Periodic notes (REST only).")


def _rest(ctx: typer.Context) -> RestApiBackend:
    config: AppConfig = config_from_ctx(ctx)
    try:
        return get_rest_backend(config)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc


@periodic_app.command("get")
def periodic_get(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
    metadata: bool = typer.Option(False, "--metadata"),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    try:
        result = rest.periodic_get(period_value, metadata=metadata)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_file_or_metadata(result)


@periodic_app.command("recent")
def periodic_recent(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
    limit: int = typer.Option(5, "--limit"),
    include_content: bool = typer.Option(False, "--include-content"),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    try:
        results = rest.periodic_recent(period_value, limit, include_content)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(results)


@periodic_app.command("write")
def periodic_write(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
    content: Optional[str] = typer.Option(None, "--content"),
    content_type: Optional[str] = typer.Option(None, "--content-type"),
    base64_input: bool = typer.Option(False, "--base64"),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    data = read_bytes_option(content, base64_input=base64_input)
    payload = build_file_payload(
        f"periodic/{period_value}",
        data,
        base64_input=base64_input,
        content_type=content_type,
    )
    try:
        rest.periodic_write(period_value, payload)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully wrote periodic {period_value} note"))


@periodic_app.command("append")
def periodic_append(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    try:
        rest.periodic_append(period_value, read_content_option(content))
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully appended to periodic {period_value} note"))


@periodic_app.command("patch")
def periodic_patch(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
    operation: OperationOption = typer.Option(..., "--operation"),
    target_type: TargetTypeOption = typer.Option(..., "--target-type"),
    target: str = typer.Option(..., "--target"),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    patch = patch_target_from_options(
        operation, target_type, target, read_content_option(content)
    )
    try:
        rest.periodic_patch(period_value, patch)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully patched periodic {period_value} note"))


@periodic_app.command("delete")
def periodic_delete(
    ctx: typer.Context,
    period: PeriodOption = typer.Argument(...),
) -> None:
    rest = _rest(ctx)
    period_value: Period = period.value  # type: ignore[assignment]
    try:
        rest.periodic_delete(period_value)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully deleted periodic {period_value} note"))

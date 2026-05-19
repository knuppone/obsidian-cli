from __future__ import annotations

from typing import Any, Optional

import typer

from obsidian_cli.cli.common import config_from_ctx, get_rest_backend
from obsidian_cli.backends.rest import RestApiBackend
from obsidian_cli.config import AppConfig
from obsidian_cli.output import emit_error, emit_json

command_app = typer.Typer(help="List and run Obsidian commands (REST only).")


def _rest(ctx: typer.Context) -> RestApiBackend:
    config: AppConfig = config_from_ctx(ctx)
    try:
        return get_rest_backend(config)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc


@command_app.command("list")
def command_list(
    ctx: typer.Context,
    filter_text: Optional[str] = typer.Option(None, "--filter", help="Substring filter on command id."),
) -> None:
    rest = _rest(ctx)
    try:
        commands: list[dict[str, Any]] = rest.list_commands()
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    if filter_text:
        needle: str = filter_text.lower()
        commands = [
            item
            for item in commands
            if needle in str(item.get("id", "")).lower()
            or needle in str(item.get("name", "")).lower()
        ]
    emit_json(dict(commands=commands))


@command_app.command("run")
def command_run(
    ctx: typer.Context,
    command_id: str = typer.Argument(..., help="Obsidian command palette id."),
) -> None:
    rest = _rest(ctx)
    try:
        rest.run_command(command_id)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(ok=True, message=f"Successfully executed command {command_id!r}"))

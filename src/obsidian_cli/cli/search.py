from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer

from obsidian_cli.cli.common import config_from_ctx, get_backend, get_rest_backend, load_json_query
from obsidian_cli.output import emit_error, emit_json

search_app = typer.Typer(help="Search vault notes.")


@search_app.command("text")
def search_text(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Text to search for."),
    context_length: int = typer.Option(100, "--context-length"),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    try:
        results: list[dict[str, Any]] = backend.search_text(query, context_length)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(results)


@search_app.command("json")
def search_json(
    ctx: typer.Context,
    query_file: Optional[Path] = typer.Argument(
        None,
        help="JsonLogic query JSON file; omit to use stdin or --tag.",
    ),
    tag: Optional[str] = typer.Option(None, "--tag", help="Build tag query without a file."),
    dirpath: Optional[str] = typer.Option(None, "--dir", help="Scope tag search to directory."),
) -> None:
    config = config_from_ctx(ctx)
    try:
        query: dict[str, Any] = load_json_query(query_file, tag, dirpath)
        results = get_rest_backend(config).search_json(query)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(results)


@search_app.command("tag")
def search_tag(
    ctx: typer.Context,
    tag: str = typer.Argument(..., help="Tag without leading #."),
    dirpath: Optional[str] = typer.Option(None, "--dir"),
) -> None:
    config = config_from_ctx(ctx)
    backend = get_backend(config)
    try:
        paths: list[str] = backend.search_tag(tag, dirpath)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(files=paths))

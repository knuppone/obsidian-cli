from __future__ import annotations

from typing import Optional

import typer

from obsidian_cli.cli.active import active_app
from obsidian_cli.cli.command import command_app
from obsidian_cli.cli.common import BackendOption, config_from_ctx, get_backend
from obsidian_cli.cli.file import file_app
from obsidian_cli.cli.periodic import periodic_app
from obsidian_cli.cli.search import search_app
from obsidian_cli.config import AppConfig, BackendKind, build_config
from obsidian_cli.output import emit_error, emit_json

app = typer.Typer(
    name="obsidian-cli",
    help="Operate on Obsidian vaults via filesystem or Local REST API.",
    no_args_is_help=True,
)

app.add_typer(file_app, name="file")
app.add_typer(search_app, name="search")
app.add_typer(active_app, name="active")
app.add_typer(periodic_app, name="periodic")
app.add_typer(command_app, name="command")


@app.callback()
def main(
    ctx: typer.Context,
    vault: Optional[str] = typer.Option(
        None,
        "--vault",
        help="Absolute path to the Obsidian vault root.",
        envvar="OBSIDIAN_VAULT",
    ),
    backend: BackendOption = typer.Option(
        BackendOption.fs,
        "--backend",
        help="fs: direct filesystem access; rest: Local REST API plugin.",
    ),
    human: bool = typer.Option(
        False,
        "--human",
        help="Human-readable output instead of JSON.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="Local REST API key (default: OBSIDIAN_API_KEY env, then vault plugin file).",
        envvar="OBSIDIAN_API_KEY",
    ),
) -> None:
    try:
        config: AppConfig = build_config(
            vault_option=vault,
            backend=BackendKind(backend.value),
            json_output=not human,
            api_key_option=api_key,
        )
    except ValueError as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    ctx.obj = dict(config=config)


@app.command("doctor")
def doctor(ctx: typer.Context) -> None:
    """Check vault resolution and REST API authentication."""
    config: AppConfig = config_from_ctx(ctx)
    report: dict[str, object] = dict(
        vault=str(config.vault_root),
        backend=config.backend.value,
    )
    if config.backend.value == "rest":
        report["api_key_source"] = config.api_key_source
        report["api_key_length"] = len(config.api_key or "")
        backend_impl = get_backend(config)
        try:
            files: list[str] = backend_impl.list_files_in_vault()
            report["rest_ok"] = True
            report["file_count"] = len(files)
        except Exception as exc:
            report["rest_ok"] = False
            report["error"] = str(exc)
    emit_json(report)


@app.command("list-root")
def list_root(ctx: typer.Context) -> None:
    """List files and directories in the vault root."""
    config = config_from_ctx(ctx)
    try:
        files = get_backend(config).list_files_in_vault()
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(files=files))


@app.command("list-dir")
def list_dir(
    ctx: typer.Context,
    dirpath: str = typer.Argument(..., help="Directory path relative to vault root."),
) -> None:
    """List files and directories in a vault subdirectory."""
    config = config_from_ctx(ctx)
    try:
        files = get_backend(config).list_files_in_dir(dirpath)
    except Exception as exc:
        emit_error(str(exc))
        raise typer.Exit(code=1) from exc
    emit_json(dict(files=files))


@app.command("read")
def read_legacy(ctx: typer.Context, filepath: str = typer.Argument(...)) -> None:
    """[alias] Use `file read` instead."""
    from obsidian_cli.cli.file import file_read

    file_read(ctx, filepath, metadata=False)


@app.command("append")
def append_legacy(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    """[alias] Use `file append` instead."""
    from obsidian_cli.cli.file import file_append

    file_append(ctx, filepath, content)


@app.command("patch")
def patch_legacy(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    operation: str = typer.Option(..., "--operation"),
    target_type: str = typer.Option(..., "--target-type"),
    target: str = typer.Option(..., "--target"),
    content: Optional[str] = typer.Option(None, "--content"),
) -> None:
    """[alias] Use `file patch` instead."""
    from obsidian_cli.cli.common import OperationOption, TargetTypeOption
    from obsidian_cli.cli.file import file_patch

    file_patch(
        ctx,
        filepath,
        OperationOption(operation),
        TargetTypeOption(target_type),
        target,
        content,
    )


@app.command("delete")
def delete_legacy(
    ctx: typer.Context,
    filepath: str = typer.Argument(...),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """[alias] Use `file delete` instead."""
    from obsidian_cli.cli.file import file_delete

    file_delete(ctx, filepath, confirm)


@app.command("search")
def search_legacy(
    ctx: typer.Context,
    query: str = typer.Argument(...),
    context_length: int = typer.Option(100, "--context-length"),
) -> None:
    """[alias] Use `search text` instead."""
    from obsidian_cli.cli.search import search_text

    search_text(ctx, query, context_length)


if __name__ == "__main__":
    app()

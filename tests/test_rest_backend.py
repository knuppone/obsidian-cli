from __future__ import annotations

import json
from typing import Any

import responses
from typer.testing import CliRunner

from obsidian_cli.backends.rest import RestApiBackend
from obsidian_cli.config import AppConfig, BackendKind
from obsidian_cli.main import app

runner: CliRunner = CliRunner()


def _rest_config() -> AppConfig:
    return AppConfig(
        vault_root=__import__("pathlib").Path("/tmp/vault"),
        backend=BackendKind.REST,
        json_output=True,
        api_key="test-key",
        host="127.0.0.1",
        port=27124,
        protocol="https",
        verify_ssl=False,
        api_key_source="env",
    )


@responses.activate
def test_rest_list_root() -> None:
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/vault/",
        json=dict(files=["a.md"]),
        status=200,
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    assert backend.list_files_in_vault() == ["a.md"]


@responses.activate
def test_rest_write_and_read() -> None:
    responses.add(
        responses.PUT,
        "https://127.0.0.1:27124/vault/note.md",
        status=204,
    )
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/vault/note.md",
        body="# Note",
        status=200,
        headers={"Content-Type": "text/markdown"},
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    from obsidian_cli.models import FilePayload

    backend.write_file("note.md", FilePayload.from_text("note.md", "# Note"))
    payload = backend.read_file("note.md")
    assert "Note" in payload.content.decode("utf-8")


@responses.activate
def test_rest_search_json() -> None:
    responses.add(
        responses.POST,
        "https://127.0.0.1:27124/search/",
        json=[dict(filename="x.md")],
        status=200,
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    results = backend.search_json({"glob": ["*.md", {"var": "path"}]})
    assert results[0]["filename"] == "x.md"


@responses.activate
def test_rest_active_read() -> None:
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/active/",
        body="# Active",
        status=200,
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    payload = backend.active_read()
    assert "Active" in payload.content.decode("utf-8")


@responses.activate
def test_rest_periodic_get() -> None:
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/periodic/daily/",
        body="# Daily",
        status=200,
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    payload = backend.periodic_get("daily")
    assert "Daily" in payload.content.decode("utf-8")


@responses.activate
def test_rest_commands() -> None:
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/commands/",
        json=dict(commands=[dict(id="app:open-settings", name="Settings")]),
        status=200,
    )
    responses.add(
        responses.POST,
        "https://127.0.0.1:27124/commands/app:open-settings/",
        status=204,
    )
    backend: RestApiBackend = RestApiBackend(_rest_config())
    commands = backend.list_commands()
    assert commands[0]["id"] == "app:open-settings"
    backend.run_command("app:open-settings")


@responses.activate
def test_cli_rest_list_root(monkeypatch: Any, tmp_path: Any) -> None:
    vault: Any = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    monkeypatch.setenv("OBSIDIAN_API_KEY", "test-key")
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/vault/",
        json=dict(files=["x.md"]),
        status=200,
    )
    result = runner.invoke(
        app,
        ["--vault", str(vault), "--backend", "rest", "list-root"],
    )
    assert result.exit_code == 0
    data: dict[str, Any] = json.loads(result.stdout)
    assert data["files"] == ["x.md"]

from __future__ import annotations

import json
from pathlib import Path

import responses

from obsidian_cli.backends.rest import RestApiBackend
from obsidian_cli.config import AppConfig, BackendKind


@responses.activate
def test_rest_retries_with_vault_key_on_401(tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    plugin_dir: Path = (
        vault / ".obsidian" / "plugins" / "obsidian-local-rest-api"
    )
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "data.json").write_text(
        json.dumps(dict(apiKey="correct-key")),
        encoding="utf-8",
    )

    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/vault/",
        json=dict(errorCode=40101, message="Authorization required"),
        status=401,
    )
    responses.add(
        responses.GET,
        "https://127.0.0.1:27124/vault/",
        json=dict(files=["a.md"]),
        status=200,
    )

    config: AppConfig = AppConfig(
        vault_root=vault,
        backend=BackendKind.REST,
        json_output=True,
        api_key="wrong-key",
        host="127.0.0.1",
        port=27124,
        protocol="https",
        verify_ssl=False,
        api_key_source="env",
    )
    backend: RestApiBackend = RestApiBackend(config)
    files: list[str] = backend.list_files_in_vault()
    assert files == ["a.md"]
    assert len(responses.calls) == 2

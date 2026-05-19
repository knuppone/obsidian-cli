from __future__ import annotations

import json
from pathlib import Path

from obsidian_cli.api_key import (
    load_api_key_from_vault,
    normalize_api_key,
    resolve_api_key,
)


def test_normalize_strips_whitespace_and_bearer() -> None:
    assert normalize_api_key("  abc  ") == "abc"
    assert normalize_api_key("Bearer xyz") == "xyz"
    assert normalize_api_key('"quoted"') == "quoted"


def test_resolve_prefers_cli_over_env(monkeypatch: object, tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_API_KEY", "from-env")
    key, source = resolve_api_key(vault, "from-cli")
    assert key == "from-cli"
    assert source == "cli"


def test_resolve_env_when_no_cli(monkeypatch: object, tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_API_KEY", "  env-key  ")
    key, source = resolve_api_key(vault, None)
    assert key == "env-key"
    assert source == "env"


def test_load_from_vault_plugin(tmp_path: Path) -> None:
    vault: Path = tmp_path / "vault"
    plugin_dir: Path = (
        vault / ".obsidian" / "plugins" / "obsidian-local-rest-api"
    )
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "data.json").write_text(
        json.dumps(dict(apiKey="vault-plugin-key")),
        encoding="utf-8",
    )
    assert load_api_key_from_vault(vault) == "vault-plugin-key"

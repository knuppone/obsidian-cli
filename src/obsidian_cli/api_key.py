from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal, Optional

ApiKeySource = Literal["cli", "env", "vault-plugin", "none"]

_PLUGIN_REL: str = ".obsidian/plugins/obsidian-local-rest-api/data.json"


def normalize_api_key(raw: str) -> str:
    key: str = raw.strip().strip('"').strip("'")
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key


def load_api_key_from_vault(vault_root: Path) -> Optional[str]:
    data_path: Path = vault_root / _PLUGIN_REL
    if not data_path.is_file():
        return None
    try:
        payload: object = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    raw: object = payload.get("apiKey") or payload.get("api_key")
    if raw is None:
        return None
    text: str = str(raw).strip()
    if not text:
        return None
    return normalize_api_key(text)


def resolve_api_key(
    vault_root: Path,
    cli_option: Optional[str],
) -> tuple[Optional[str], ApiKeySource]:
    if cli_option is not None and cli_option.strip():
        return normalize_api_key(cli_option), "cli"

    env_raw: Optional[str] = os.getenv("OBSIDIAN_API_KEY")
    if env_raw is not None and env_raw.strip():
        return normalize_api_key(env_raw), "env"

    from_vault: Optional[str] = load_api_key_from_vault(vault_root)
    if from_vault:
        return from_vault, "vault-plugin"

    return None, "none"

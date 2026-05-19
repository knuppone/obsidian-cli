from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from obsidian_cli.api_key import ApiKeySource, resolve_api_key


class BackendKind(str, Enum):
    FS = "fs"
    REST = "rest"


@dataclass(frozen=True)
class AppConfig:
    vault_root: Path
    backend: BackendKind
    json_output: bool
    api_key: Optional[str]
    host: str
    port: int
    protocol: str
    verify_ssl: bool
    api_key_source: ApiKeySource


def _find_vault_from_cwd() -> Optional[Path]:
    current: Path = Path.cwd().resolve()
    for parent in (current, *current.parents):
        if (parent / ".obsidian").is_dir():
            return parent
    return None


def resolve_vault_root(vault_option: Optional[str]) -> Path:
    if vault_option:
        path: Path = Path(vault_option).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Vault path is not a directory: {path}")
        return path

    env_vault: Optional[str] = os.getenv("OBSIDIAN_VAULT")
    if env_vault:
        path = Path(env_vault).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"OBSIDIAN_VAULT is not a directory: {path}")
        return path

    from_cwd: Optional[Path] = _find_vault_from_cwd()
    if from_cwd is not None:
        return from_cwd

    raise ValueError(
        "Could not resolve vault. Set --vault, OBSIDIAN_VAULT, or run inside a vault."
    )


def build_config(
    vault_option: Optional[str],
    backend: BackendKind,
    json_output: bool,
    api_key_option: Optional[str] = None,
) -> AppConfig:
    vault_root: Path = resolve_vault_root(vault_option)
    api_key, api_key_source = resolve_api_key(vault_root, api_key_option)
    if backend == BackendKind.REST and not api_key:
        raise ValueError(
            "API key required for --backend rest. Set OBSIDIAN_API_KEY, pass "
            "--api-key, or install the Local REST API plugin in this vault."
        )

    protocol: str = os.getenv("OBSIDIAN_PROTOCOL", "https").lower()
    verify_ssl: bool = os.getenv("OBSIDIAN_VERIFY_SSL", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    return AppConfig(
        vault_root=vault_root,
        backend=backend,
        json_output=json_output,
        api_key=api_key,
        host=os.getenv("OBSIDIAN_HOST", "127.0.0.1"),
        port=int(os.getenv("OBSIDIAN_PORT", "27124")),
        protocol=protocol if protocol in ("http", "https") else "https",
        verify_ssl=verify_ssl,
        api_key_source=api_key_source,
    )

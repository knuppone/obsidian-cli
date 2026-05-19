from __future__ import annotations

from pathlib import Path

SKIP_DIR_NAMES: frozenset[str] = frozenset({".obsidian", ".git", ".trash"})


class PathEscapeError(ValueError):
    pass


def normalize_vault_relative(relative: str) -> str:
    cleaned: str = relative.strip().replace("\\", "/")
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    parts: list[str] = []
    for segment in cleaned.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            raise PathEscapeError(f"Path escapes vault root: {relative!r}")
        parts.append(segment)
    return "/".join(parts)


def resolve_in_vault(vault_root: Path, relative: str) -> Path:
    normalized: str = normalize_vault_relative(relative)
    candidate: Path = (vault_root / normalized).resolve()
    root_resolved: Path = vault_root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise PathEscapeError(f"Path escapes vault root: {relative!r}") from exc
    return candidate


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")

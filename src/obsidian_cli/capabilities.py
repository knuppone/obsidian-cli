from __future__ import annotations

from obsidian_cli.config import BackendKind

REST_ONLY_FEATURES: frozenset[str] = frozenset(
    {
        "json_search",
        "active_file",
        "periodic_notes",
        "commands",
    }
)


def require_rest(backend: BackendKind, feature: str) -> None:
    from obsidian_cli.errors import RestOnlyError

    if backend == BackendKind.FS:
        raise RestOnlyError(feature)

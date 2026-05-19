from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from obsidian_cli.paths import should_skip_dir

TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md",
        ".markdown",
        ".txt",
        ".canvas",
        ".json",
    }
)


def _is_searchable_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return path.suffix == ""


def simple_search(
    vault_root: Path,
    query: str,
    context_length: int = 100,
) -> List[Dict[str, Any]]:
    query_lower: str = query.lower()
    results: List[Dict[str, Any]] = []

    for file_path in vault_root.rglob("*"):
        if not file_path.is_file():
            continue
        if not _is_searchable_file(file_path):
            continue

        rel_parts: tuple[str, ...] = file_path.relative_to(vault_root).parts
        if any(should_skip_dir(part) for part in rel_parts[:-1]):
            continue
        if any(part.startswith(".") for part in rel_parts):
            continue

        try:
            text: str = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        text_lower: str = text.lower()
        start: int = 0
        file_matches: List[Dict[str, Any]] = []
        while True:
            index: int = text_lower.find(query_lower, start)
            if index < 0:
                break
            context_start: int = max(0, index - context_length)
            context_end: int = min(len(text), index + len(query) + context_length)
            context: str = text[context_start:context_end]
            match_start_in_context: int = index - context_start
            file_matches.append(
                dict(
                    context=context,
                    match_position=dict(
                        start=match_start_in_context,
                        end=match_start_in_context + len(query),
                    ),
                )
            )
            start = index + len(query)

        if file_matches:
            rel_path: str = file_path.relative_to(vault_root).as_posix()
            results.append(
                dict(
                    filename=rel_path,
                    score=0,
                    matches=file_matches,
                )
            )

    return results

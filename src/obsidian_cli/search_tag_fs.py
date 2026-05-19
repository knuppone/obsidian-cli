from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set

from obsidian_cli.patch.frontmatter import split_frontmatter
from obsidian_cli.paths import should_skip_dir
from obsidian_cli.search_fs import TEXT_EXTENSIONS, _is_searchable_file

_INLINE_TAG_RE = re.compile(r"(?<!\w)#([a-zA-Z][\w/-]*)")


def _tags_from_content(content: str) -> Set[str]:
    tags: Set[str] = set()
    frontmatter, body, had_fm = split_frontmatter(content)
    if had_fm:
        raw_tags: object = frontmatter.get("tags")
        if isinstance(raw_tags, str):
            tags.add(raw_tags.strip())
        elif isinstance(raw_tags, list):
            for item in raw_tags:
                tags.add(str(item).strip())
    for match in _INLINE_TAG_RE.finditer(body):
        tags.add(match.group(1))
    return tags


def search_by_tag(
    vault_root: Path,
    tag: str,
    dirpath: str | None = None,
) -> List[str]:
    normalized_tag: str = tag.lstrip("#")
    prefix: str = ""
    if dirpath:
        prefix = dirpath.rstrip("/") + "/"

    matches: List[str] = []
    for file_path in vault_root.rglob("*"):
        if not file_path.is_file() or not _is_searchable_file(file_path):
            continue
        rel: str = file_path.relative_to(vault_root).as_posix()
        rel_parts: tuple[str, ...] = file_path.relative_to(vault_root).parts
        if any(should_skip_dir(part) for part in rel_parts[:-1]):
            continue
        if any(part.startswith(".") for part in rel_parts):
            continue
        if prefix and not rel.startswith(prefix):
            continue
        try:
            text: str = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if normalized_tag in _tags_from_content(text):
            matches.append(rel)
    return sorted(matches)

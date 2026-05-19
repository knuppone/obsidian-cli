from __future__ import annotations

import re
from typing import List, Tuple

_BLOCK_ID_RE = re.compile(r"\^([a-zA-Z0-9_-]+)\s*$")


def _find_block_range(lines: List[str], block_id: str) -> Tuple[int, int]:
    block_line_index: int = -1
    for index, line in enumerate(lines):
        match = _BLOCK_ID_RE.search(line.rstrip("\n\r"))
        if match and match.group(1) == block_id:
            block_line_index = index
            break

    if block_line_index < 0:
        raise ValueError(f"Block not found: {block_id!r}")

    start_index: int = block_line_index
    while start_index > 0:
        prev: str = lines[start_index - 1].strip()
        if prev == "" or prev.startswith("#"):
            break
        start_index -= 1

    end_index: int = block_line_index + 1
    while end_index < len(lines):
        nxt: str = lines[end_index].strip()
        if nxt == "":
            break
        if nxt.startswith("#"):
            break
        if _BLOCK_ID_RE.search(nxt):
            break
        end_index += 1

    return start_index, end_index


def patch_block(content: str, operation: str, block_id: str, patch_text: str) -> str:
    lines: List[str] = content.splitlines(keepends=True)
    if not lines and content:
        lines = [content]

    start_index, end_index = _find_block_range(lines, block_id)
    prefix: str = "".join(lines[:start_index])
    block_lines: List[str] = lines[start_index:end_index]
    suffix: str = "".join(lines[end_index:])
    existing: str = "".join(block_lines)

    if operation == "replace":
        merged = patch_text
    elif operation == "prepend":
        merged = patch_text + existing
    else:
        merged = existing + patch_text

    if merged and not merged.endswith("\n") and suffix:
        merged += "\n"
    return prefix + merged + suffix

from __future__ import annotations

import re
from typing import List, Tuple

_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def find_heading_paths(content: str, target: str) -> List[str]:
    in_fence: bool = False
    stack: List[Tuple[int, str]] = []
    matches: List[str] = []
    target_lower: str = target.lower()

    for line in content.split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(line)
        if not match:
            continue
        level: int = len(match.group(1))
        text: str = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, text))
        if text.lower() == target_lower:
            matches.append("::".join(title for _, title in stack))

    return matches


def _parse_heading_line(line: str) -> Tuple[int, str] | None:
    match = _HEADING_RE.match(line)
    if not match:
        return None
    level: int = len(match.group(1))
    text: str = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
    return level, text


def _heading_stack_matches(stack: List[Tuple[int, str]], qualified: str) -> bool:
    parts: List[str] = qualified.split("::")
    if len(parts) != len(stack):
        return False
    return all(a.lower() == b.lower() for a, b in zip(parts, (t for _, t in stack)))


def _section_end_index(lines: List[str], heading_index: int, heading_level: int) -> int:
    in_fence: bool = False
    for index in range(heading_index + 1, len(lines)):
        line: str = lines[index]
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        parsed = _parse_heading_line(line)
        if parsed is not None and parsed[0] <= heading_level:
            return index
    return len(lines)


def _locate_heading_section(
    lines: List[str], qualified: str
) -> Tuple[int, int, int]:
    in_fence: bool = False
    stack: List[Tuple[int, str]] = []

    for index, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        parsed = _parse_heading_line(line)
        if parsed is None:
            continue
        level, text = parsed
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, text))
        if _heading_stack_matches(stack, qualified):
            end_index: int = _section_end_index(lines, index, level)
            return index, index + 1, end_index

    raise ValueError(f"Heading not found: {qualified!r}")


def patch_heading(
    content: str,
    operation: str,
    qualified: str,
    patch_text: str,
) -> str:
    lines: List[str] = content.splitlines(keepends=True)
    if not lines and content == "":
        lines = []

    body_start: int
    body_end: int
    try:
        _, body_start, body_end = _locate_heading_section(lines, qualified)
    except ValueError:
        if content and not content.endswith("\n"):
            lines = [content + "\n"]
        else:
            lines = list(lines) if lines else []
        heading_line: str = _qualified_to_heading_line(qualified)
        if operation == "replace":
            return heading_line + patch_text
        if operation == "prepend":
            return heading_line + patch_text + "\n"
        return heading_line + "\n" + patch_text

    section_body: List[str] = lines[body_start:body_end]
    prefix: str = "".join(lines[:body_start])
    suffix: str = "".join(lines[body_end:])

    if operation == "replace":
        new_body: str = patch_text
        if new_body and not new_body.endswith("\n") and suffix:
            new_body += "\n"
        return prefix + new_body + suffix

    existing: str = "".join(section_body)
    if operation == "prepend":
        merged: str = patch_text + existing
    else:
        merged = existing + patch_text

    if merged and not merged.endswith("\n") and suffix:
        merged += "\n"
    return prefix + merged + suffix


def _qualified_to_heading_line(qualified: str) -> str:
    parts: List[str] = qualified.split("::")
    depth: int = min(len(parts), 6)
    return "#" * depth + " " + parts[-1] + "\n"

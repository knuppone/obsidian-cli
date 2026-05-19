from __future__ import annotations

import re
from io import StringIO
from typing import Any, Dict, List, Tuple

from ruamel.yaml import YAML

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _yaml_loader() -> YAML:
    yaml: YAML = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    return yaml


def split_frontmatter(content: str) -> Tuple[Dict[str, Any], str, bool]:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return dict(), content, False

    yaml = _yaml_loader()
    parsed: Any = yaml.load(match.group(1))
    if parsed is None:
        data: Dict[str, Any] = dict()
    elif isinstance(parsed, dict):
        data = dict(parsed)
    else:
        raise ValueError("Frontmatter must be a YAML mapping.")

    body: str = content[match.end() :]
    return data, body, True


def _dump_frontmatter(data: Dict[str, Any]) -> str:
    yaml = _yaml_loader()
    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue().rstrip("\n")


def _apply_field_operation(
    current: Any, operation: str, patch_text: str
) -> Any:
    if operation == "replace":
        stripped: str = patch_text.rstrip("\n")
        if stripped.startswith("[") and stripped.endswith("]"):
            inner: str = stripped[1:-1].strip()
            if not inner:
                return list()
            return [item.strip().strip("'\"") for item in inner.split(",")]
        return patch_text.rstrip("\n")

    if current is None:
        base: str = ""
    elif isinstance(current, list):
        base = "\n".join(str(item) for item in current)
    else:
        base = str(current)

    if operation == "prepend":
        return patch_text + base
    return base + patch_text


def patch_frontmatter(
    content: str, operation: str, field: str, patch_text: str
) -> str:
    data, body, had_fm = split_frontmatter(content)
    data[field] = _apply_field_operation(data.get(field), operation, patch_text)
    fm_block: str = f"---\n{_dump_frontmatter(data)}\n---\n"
    if had_fm or body:
        return fm_block + body
    return fm_block

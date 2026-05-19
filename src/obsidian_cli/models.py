from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

EncodingKind = Literal["utf-8", "base64"]

DEFAULT_TEXT_CONTENT_TYPE: str = "text/markdown; charset=utf-8"
NOTE_JSON_ACCEPT: str = "application/vnd.olrapi.note+json"
JSONLOGIC_CONTENT_TYPE: str = "application/vnd.olrapi.jsonlogic+json"

Period = Literal["daily", "weekly", "monthly", "quarterly", "yearly"]
VALID_PERIODS: tuple[str, ...] = ("daily", "weekly", "monthly", "quarterly", "yearly")


@dataclass(frozen=True)
class FilePayload:
    path: str
    content: bytes
    is_binary: bool
    content_type: Optional[str] = None

    @property
    def encoding(self) -> EncodingKind:
        return "base64" if self.is_binary else "utf-8"

    def to_json_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = dict(
            path=self.path,
            encoding=self.encoding,
            size=len(self.content),
        )
        if self.content_type:
            result["content_type"] = self.content_type
        if self.is_binary:
            result["content"] = base64.b64encode(self.content).decode("ascii")
        else:
            result["content"] = self.content.decode("utf-8")
        return result

    @classmethod
    def from_text(cls, path: str, text: str, content_type: Optional[str] = None) -> FilePayload:
        return cls(
            path=path,
            content=text.encode("utf-8"),
            is_binary=False,
            content_type=content_type or DEFAULT_TEXT_CONTENT_TYPE,
        )

    @classmethod
    def from_bytes(
        cls,
        path: str,
        data: bytes,
        *,
        is_binary: bool = True,
        content_type: Optional[str] = None,
    ) -> FilePayload:
        return cls(path=path, content=data, is_binary=is_binary, content_type=content_type)


@dataclass
class PatchTarget:
    operation: str
    target_type: str
    target: str
    content: str
    target_scope: Optional[str] = None


@dataclass
class NoteMetadata:
    path: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    content: str = ""
    tags: list[str] = field(default_factory=list)

    def to_json_dict(self) -> Dict[str, Any]:
        return dict(
            path=self.path,
            frontmatter=self.frontmatter,
            tags=self.tags,
            content=self.content,
        )

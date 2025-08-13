from __future__ import annotations

from enum import Enum
from typing import List, Optional

try:  # pydantic v2
    from pydantic import BaseModel, Field
    V2 = True
except Exception:  # pragma: no cover - fallback to v1
    from pydantic.v1 import BaseModel, Field  # type: ignore
    V2 = False


class ChangeType(str, Enum):
    Add = "Add"
    Delete = "Delete"
    Rename = "Rename"
    Modify = "Modify"


class HunkType(str, Enum):
    Add = "Add"
    Delete = "Delete"
    Modify = "Modify"


class LineOperation(str, Enum):
    Add = "Add"
    Delete = "Delete"


class LineChangeDTO(BaseModel):
    operation: LineOperation
    number: int
    content: Optional[str] = None


class HunkDTO(BaseModel):
    added_line_changes: List[LineChangeDTO] = Field(default_factory=list)
    deleted_line_changes: List[LineChangeDTO] = Field(default_factory=list)

    @property
    def type(self) -> HunkType:
        if not self.added_line_changes:
            return HunkType.Delete
        if not self.deleted_line_changes:
            return HunkType.Add
        return HunkType.Modify

    @property
    def line_changes(self) -> List[LineChangeDTO]:
        return list(self.added_line_changes) + list(self.deleted_line_changes)


class ChangeDTO(BaseModel):
    old_file_name: str
    new_file_name: str
    type: ChangeType
    parent_commit_id: str
    binary: bool
    hunks: List[HunkDTO] = Field(default_factory=list)


class CommitDTO(BaseModel):
    id: str
    parent_ids: List[str]
    author_date: str
    author_email: str
    author_name: str
    committer_date: str
    committer_email: str
    committer_name: str
    message: str
    changes: List[ChangeDTO] = Field(default_factory=list)


class GitLogDTO(BaseModel):
    ig_log_version: Optional[str]
    name: str
    commits: List[CommitDTO] = Field(default_factory=list)


# Human-readable representation helpers
if V2:
    def to_pretty_json(obj: BaseModel) -> str:
        # Pydantic v2: model_dump_json doesn't support ensure_ascii; defaults to UTF-8
        return obj.model_dump_json(indent=2)
else:  # v1
    import json

    def to_pretty_json(obj: BaseModel) -> str:  # type: ignore
        return json.dumps(obj.dict(), indent=2, ensure_ascii=False)


__all__ = [
    "ChangeType",
    "HunkType",
    "LineOperation",
    "LineChangeDTO",
    "HunkDTO",
    "ChangeDTO",
    "CommitDTO",
    "GitLogDTO",
    "to_pretty_json",
]

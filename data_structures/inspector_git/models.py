from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import ChangeType, HunkType, LineOperation

class LineChangeDTO(BaseModel):
    """Represents a line change in a hunk."""
    operation: LineOperation
    number: int
    content: Optional[str] = None

class HunkDTO(BaseModel):
    """Represents a hunk of changes in a file."""
    added_line_changes: List[LineChangeDTO] = Field(default_factory=list)
    deleted_line_changes: List[LineChangeDTO] = Field(default_factory=list)
    
    @property
    def type(self) -> HunkType:
        """Get the type of the hunk based on the line changes."""
        if not self.added_line_changes:
            return HunkType.Delete
        if not self.deleted_line_changes:
            return HunkType.Add
        return HunkType.Modify
    
    @property
    def line_changes(self) -> List[LineChangeDTO]:
        """Get all line changes in the hunk."""
        return self.added_line_changes + self.deleted_line_changes

class ChangeDTO(BaseModel):
    """Represents a file change in a commit."""
    old_file_name: str
    new_file_name: str
    type: ChangeType
    parent_commit_id: str
    binary: bool
    hunks: List[HunkDTO] = Field(default_factory=list)

class CommitDTO(BaseModel):
    """Represents a Git commit."""
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
    """Represents a Git log."""
    ig_log_version: str
    name: str
    commits: List[CommitDTO] = Field(default_factory=list)
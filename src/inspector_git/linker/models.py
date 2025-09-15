from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from abc import ABC, abstractmethod
from src.inspector_git.linker.registry import AccountRegistry, CommitRegistry, FileRegistry
from typing import List, Type, TypeVar, Optional
import uuid
from src.inspector_git.utils.constants import DEV_NULL
from datetime import datetime, timedelta

class Account(BaseModel, ABC):
    name: str
    project: Project
    developer: Optional[Developer] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    @abstractmethod
    def id(self) -> str:
        ...

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, Account):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)



class GitAccountId(BaseModel):
    email: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

class GitAccount(Account):
    git_id: GitAccountId
    commits: List[Commit] = Field(default_factory=list)

    # this runs after init, before validation is done
    @model_validator(mode="before")
    @classmethod
    def set_account_fields(cls, data: dict):
        """
        Ensure that 'name' and 'project' are properly set
        based on git_id and git_project.
        """
        if isinstance(data, dict):
            git_id = data.get("git_id")
            git_project = data.get("project") or data.get("git_project")

            if git_id is not None:
                # set the inherited 'name' from git_id
                if "name" not in data:
                    data["name"] = git_id.name
            if git_project is not None:
                # normalize: accept 'git_project' as 'project'
                data["project"] = git_project

        return data

    @property
    def id(self) -> str:
        return str(self.git_id)

    @property
    def changes(self) -> List[Change]:
        return [change for commit in self.commits for change in commit.changes]

    @property
    def files(self) -> List[File]:
        return list({change.file for change in self.changes})

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, GitAccount):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return str(self.git_id)

AccountType = TypeVar("AccountType", bound=Account)
class Developer(BaseModel):
    name: str
    accounts: list[Account] = Field(default_factory=list)

    def get_accounts_of_type(self, account_type: Type[AccountType]) -> list[AccountType]:
        return [account for account in self.accounts if isinstance(account, account_type)]

    class Config:
        arbitrary_types_allowed = True

class Project(BaseModel, ABC):
    linked_projects: set[Project] = Field(default_factory=set)

    class Config:
        arbitrary_types_allowed = True

    def link(self, other: Project) -> None:
        self.linked_projects.add(other)

    def is_linked(self, other: Project) -> bool:
        return other in self.linked_projects

class GitProject(Project):
    name: str
    account_registry: AccountRegistry = Field(default_factory=AccountRegistry)
    commit_registry: CommitRegistry = Field(default_factory=CommitRegistry)
    file_registry: FileRegistry = Field(default_factory=FileRegistry)

    model_config = {"arbitrary_types_allowed": True}

class LineOperation(Enum):
    ADD = "ADD"
    DELETE = "DELETE"

class ChangeType(Enum):
    ADD = "ADD"
    DELETE = "DELETE"
    RENAME = "RENAME"
    MODIFY = "MODIFY"

class LineChange(BaseModel):
    operation: LineOperation
    line_number: int
    commit: Commit

    def __eq__(self, other):
        if not isinstance(other, LineChange):
            return False
        return (
                self.operation == other.operation and
                self.line_number == other.line_number
        )

    def __hash__(self):
        # Only use immutable fields
        return hash((self.operation, self.line_number))

class Hunk(BaseModel):
    line_changes: List[LineChange]
    deleted_lines: List[LineChange] = []
    added_lines: List[LineChange] = []

    @model_validator(mode="after")
    @classmethod
    def derive_added_deleted(cls, values):
        line_changes = values.line_changes
        values.deleted_lines = [lc for lc in line_changes if lc.operation == LineOperation.DELETE]
        values.added_lines = [lc for lc in line_changes if lc.operation == LineOperation.ADD]
        return values
    def __hash__(self):
        return hash((
            tuple(self.line_changes),
            tuple(self.deleted_lines),
            tuple(self.added_lines),
        ))

    def __eq__(self, other):
        if not isinstance(other, Hunk):
            return False
        return (
                self.line_changes == other.line_changes and
                self.deleted_lines == other.deleted_lines and
                self.added_lines == other.added_lines
        )

class File(BaseModel):
    is_binary: bool
    project: GitProject
    changes: List[Change] = Field(default_factory=list)
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    class Config:
        arbitrary_types_allowed = True

    def is_alive(self, commit: Optional[Commit] = None) -> bool:
        last = self.get_last_change(commit)
        typ = last.change_type if last is not None else None
        return typ is not None and typ is not ChangeType.DELETE

    def annotated_lines(self, commit: Optional[Commit] = None) -> List[Commit]:
        last = self.get_last_change(commit)
        return last.annotated_lines if (last is not None and getattr(last, "annotated_lines", None) is not None) else []

    def full_path(self, commit: Optional[Commit] = None) -> Optional[str]:
        last = self.get_last_change(commit)
        if last is None:
            return None
        new_file_name = getattr(last, "new_file_name", None)
        return f"{self.project.name}/{new_file_name}" if new_file_name is not None else None

    def file_name(self, commit: Optional[Commit] = None) -> Optional[str]:
        rel = self.relative_path(commit)
        if rel is None:
            return None
        if rel == DEV_NULL:
            return rel
        idx = rel.rfind("/")
        return rel if idx == -1 else rel[idx + 1 :]

    def relative_path(self, commit: Optional[Commit] = None) -> Optional[str]:
        last = self.get_last_change(commit)
        return getattr(last, "new_file_name", None) if last is not None else None

    def get_last_change(self, commit: Optional[Commit] = None) -> Optional[Change]:
        if not self.changes:
            return None
        if commit is None:
            return self.changes[-1]
        return self._get_last_change_recursively(commit)

    def _get_last_change_recursively(self, commit: Commit) -> Optional[Change]:
        found = next((c for c in self.changes if getattr(c, "commit", None) == commit), None)
        if found is not None:
            return found
        parents = getattr(commit, "parents", None)
        if not parents:
            return None
        parent = parents[0] if len(parents) > 0 else None
        if parent is None:
            return None
        return self._get_last_change_recursively(parent)

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, File):
            return False
        return self.is_binary == other.is_binary and self.id == other.id

    def __hash__(self) -> int:
        result = hash(self.is_binary)
        result = 31 * result + hash(self.id)
        return result

    def __str__(self) -> str:
        return str(self.changes[-1].new_file_name if self.changes else "nu stiu")

class Commit(BaseModel):
    project: GitProject
    id: str
    message: str
    author_date: datetime
    committer_date: datetime
    author: GitAccount
    committer: GitAccount
    parents: List[Commit] = Field(default_factory=list)
    children: List[Commit] = Field(default_factory=list)
    changes: List[Change] = Field(default_factory=list)
    # issues: Set[Issue] = Field(default_factory=set)
    # pull_requests: Set[PullRequest] = Field(default_factory=set)
    # remote_info: Optional[CommitRemoteInfo] = None
    branch_id: int = 0
    repo_size: int = 0

    class Config:
        arbitrary_types_allowed = True

    def older_than(self, age: timedelta, other: Commit) -> bool:
        try:
            threshold = other.committer_date - age
        except Exception:
            # If subtraction fails, propagate the error so callers know the type is incompatible.
            raise
        return self.committer_date < threshold

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, Commit):
            return False
        return (
            self.id == other.id
            and self.message == other.message
            and self.author_date == other.author_date
            and self.committer_date == other.committer_date
            and self.author == other.author
            and self.committer == other.committer
        )

    def __hash__(self) -> int:
        result = hash(self.id)
        result = 31 * result + hash(self.message)
        result = 31 * result + hash(self.author_date)
        result = 31 * result + hash(self.committer_date)
        result = 31 * result + hash(self.author)
        result = 31 * result + hash(self.committer)
        return result

    @property
    def is_merge_commit(self) -> bool:
        return len(self.parents) > 1

    @property
    def is_split_commit(self) -> bool:
        return len(self.children) > 1

    def add_child(self, commit: Commit) -> None:
        self.children = [*self.children, commit]

    def is_after_in_tree(self, other: Commit) -> bool:
        if other in self.parents:
            return True
        return any(parent.is_after_in_tree(other) for parent in self.parents)

    def __str__(self) -> str:
        return self.id

class Change(BaseModel):
    commit: Commit
    change_type: ChangeType
    old_file_name: str
    new_file_name: str
    file: File
    parent_commit: Optional[Commit] = None
    hunks: List[Hunk] = Field(default_factory=list)
    annotated_lines: List[Commit] = Field(default_factory=list)
    parent_change: Optional[Change] = None
    compute_annotated_lines: bool = False

    class Config:
        arbitrary_types_allowed = True

    @property
    def id(self) -> str:
        return f"{self.commit.id}-{self.old_file_name}->{self.new_file_name}"

    @property
    def line_changes(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.line_changes]

    @property
    def deleted_lines(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.deleted_lines]

    @property
    def added_lines(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.added_lines]

    def __init__(self, **data):
        super().__init__(**data)
        if not self.file.is_binary and self.compute_annotated_lines:
            self._apply_line_changes(self.parent_change)

    def _apply_line_changes(self, parent_change: Optional["Change"]) -> None:
        try:
            new_annotated_lines = list(parent_change.annotated_lines) if parent_change else []
            deletes = self.deleted_lines
            adds = self.added_lines
            for d in sorted(deletes, key=lambda x: x.line_number, reverse=True):
                new_annotated_lines.pop(d.line_number - 1)
            for a in adds:
                new_annotated_lines.insert(a.line_number - 1, a.commit)
            self.annotated_lines = new_annotated_lines
        except IndexError:
            self.file.is_binary = True


    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, Change):
            return False
        return (
                self.change_type == other.change_type
                and self.file == other.file
                and self.line_changes == other.line_changes
                and self.annotated_lines == other.annotated_lines
        )

    def __hash__(self) -> int:
        result = hash(self.change_type)
        result = 31 * result + hash(self.commit)
        result = 31 * result + hash(self.old_file_name)
        result = 31 * result + hash(self.new_file_name)
        result = 31 * result + hash(tuple(self.hunks))
        result = 31 * result + hash(tuple(self.annotated_lines))
        return result

    def __str__(self) -> str:
        return (f"In {self.commit.id} : {self.commit.message}\n"
                f"{self.change_type} {self.old_file_name}->{self.new_file_name}")

LineChange.model_rebuild()
Hunk.model_rebuild()
GitAccountId.model_rebuild()
File.model_rebuild()
Commit.model_rebuild()
Change.model_rebuild()

__all__ = [
    "Account",
    "Developer",
    "Project",
    "GitProject",
    "LineOperation",
    "ChangeType",
    "LineChange",
    "Hunk",
    "GitAccountId",
    "GitAccount",
    "File",
    "Commit",
    "Change",
]








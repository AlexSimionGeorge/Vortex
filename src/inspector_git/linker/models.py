from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from src.common.models import Project, Account
from src.inspector_git.linker.registry import AccountRegistry, CommitRegistry, FileRegistry, ChangeRegistry
from typing import List, Optional, Collection
import uuid
from src.inspector_git.utils.constants import DEV_NULL
from datetime import datetime, timedelta
from src.logger import get_logger

LOG = get_logger(__name__)

class GitAccountId(BaseModel):
    email: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

class GitAccount(Account):
    git_id: GitAccountId
    commits: List[Commit] = Field(default_factory=list)

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

    def __reduce__(self):
        state = (self.git_id, [c.id for c in self.commits])
        return self._rebuild, state

    @classmethod
    def _rebuild(cls, id: GitAccountId, commits: List[str]):
        obj = cls(git_id=id, name=id.name)
        obj._commits = commits
        return obj

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

class GitProject(Project):
    name: str
    account_registry: AccountRegistry = Field(default_factory=AccountRegistry)
    commit_registry: CommitRegistry = Field(default_factory=CommitRegistry)
    file_registry: FileRegistry = Field(default_factory=FileRegistry)
    change_registry: ChangeRegistry = Field(default_factory=ChangeRegistry)

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return (
            f"account reg: {len(self.account_registry.all)},\n"
            f"commit reg: {len(self.commit_registry.all)},\n"
            f"file reg: {len(self.file_registry.all)},\n"
            f"change reg: {len(self.change_registry.all)}"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GitProject):
            return NotImplemented
        return (
                self.name == other.name
                and self.account_registry._map == other.account_registry._map
                and self.commit_registry._map == other.commit_registry._map
                and self.file_registry._map == other.file_registry._map
                and self.change_registry._map == other.change_registry._map
        )

    def _relink_objects(self):
        for account in self.account_registry.all:
            for c in account._commits:
                commit = self.commit_registry.get_by_id(c)
                if commit is None:
                    LOG.warning(f"Could not find commit {c} in commit registry")
                account.commits.append(commit)
        del account._commits

        for commit in self.commit_registry.all:
            author = self.account_registry.get_by_id(commit._author.__str__())
            if author is None:
                LOG.warning(f"Could not find author {commit._author} in account registry")
            commit.author = author

            committer = self.account_registry.get_by_id(commit._committer.__str__())
            if committer is None:
                LOG.warning(f"Could not find committer {commit._committer} in account registry")
            commit.committer = committer

            for p in commit._parents:
                parent = self.commit_registry.get_by_id(p)
                if parent is None:
                    LOG.warning(f"Could not find parent {p} in commit registry")
                commit.parents.append(parent)

            for c in commit._children:
                child = self.commit_registry.get_by_id(c)
                if child is None:
                    LOG.warning(f"Could not find child {c} in commit registry")
                commit.children.append(child)

            for c in commit._changes:
                change = self.change_registry.get_by_id(c)
                if change is None:
                    LOG.warning(f"Could not find change {c} in change registry")
                commit.changes.append(change)

            del commit._author
            del commit._committer
            del commit._parents
            del commit._children
            del commit._changes

        for file in self.file_registry.all:
            for c in file._changes:
                change = self.change_registry.get_by_id(c)
                if change is None:
                    LOG.warning(f"Could not find change {c} in change registry")
                file.changes.append(change)

            del file._changes

        for change in self.change_registry.all:
            commit = self.commit_registry.get_by_id(change._commit) # should field _commit must exist
            if commit is None:
                LOG.warning(f"Could not find commit {change._commit} in commit registry")
            change.commit = commit

            file = self.file_registry.get_by_id(change._file) # should field _file must exist
            if file is None:
                LOG.warning(f"Could not find file {change._file} in file registry")
            change.file = file

            if change._parent_commit is not None:
                parent_commit = self.commit_registry.get_by_id(change._parent_commit)
                if parent_commit is None:
                    LOG.warning(f"Could not find parent commit {change._parent_commit} in commit registry")
                change.parent_commit = parent_commit

            for c in change._annotated_lines:
                commit = self.commit_registry.get_by_id(c)
                if commit is None:
                    LOG.warning(f"Could not find commit {c} in commit registry")
                change.annotated_lines.append(commit)

            if change._parent_change is not None:
                parent_change = self.change_registry.get_by_id(change._parent_change)
                if parent_change is None:
                    LOG.warning(f"Could not find parent change {change._parent_change} in change registry")
                change.parent_change = parent_change

            del change._commit
            del change._file
            del change._parent_commit
            del change._annotated_lines
            del change._parent_change

    def __reduce__(self):
        state = (
            self.name,
            list(self.account_registry.all),
            list(self.commit_registry.all),
            list(self.file_registry.all),
            list(self.change_registry.all),
        )
        return self._rebuild, state

    @classmethod
    def _rebuild(
        cls,
        name: str,
        accounts: Collection[GitAccount],
        commits: Collection[Commit],
        files: Collection[File],
        changes: Collection[Change],
    ):
        # Create empty registries
        obj = cls(
            name=name,
            account_registry=AccountRegistry(),
            commit_registry=CommitRegistry(),
            file_registry=FileRegistry(),
            change_registry=ChangeRegistry(),
        )

        # Fill registries from the saved collections
        obj.account_registry.add_all(accounts)
        obj.commit_registry.add_all(commits)
        obj.file_registry.add_all(files)
        obj.change_registry.add_all(changes)

        obj._relink_objects()

        return obj

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
    project: Optional[GitProject] = None
    changes: List[Change] = Field(default_factory=list)
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    class Config:
        arbitrary_types_allowed = True

    def __reduce__(self):
        # Instead of storing Student objects, store only IDs
        state = (self.is_binary,
                 [c.id for c in self.changes],
                 self.id)
        return self._rebuild, state

    @classmethod
    def _rebuild(
            cls,
            is_binary: bool,
            change_ids: List[uuid.UUID],
            id: uuid.UUID,
    ):
        obj = cls(
            is_binary=is_binary,
            changes=[],
            id=id,
        )
        obj._changes = change_ids
        return obj

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
    project: Optional[GitProject] = None
    id: str
    message: str
    author_date: datetime
    committer_date: datetime
    author: Optional[GitAccount] = None # this is optional to not cause problems in the loading process after serialization
    committer: Optional[GitAccount] = None # same as above
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

    def __reduce__(self):
        state = (self.id,
                 self.message,
                 self.author_date,
                 self.committer_date,
                 self.author.git_id,
                 self.committer.git_id,
                 [p.id for p in self.parents],
                 [c.id for c in self.children],
                 [c.id for c in self.changes],
                 self.branch_id,
                 self.repo_size,)
        return self._rebuild, state

    @classmethod
    def _rebuild(
            cls,
            id: str,
            message: str,
            author_date: datetime,
            committer_date: datetime,
            author_id: GitAccountId,
            committer_id: GitAccountId,
            parent_ids: List[str],
            child_ids: List[str],
            change_ids: List[str],
            branch_id: int,
            repo_size: int,
    ):
        obj = cls(
            id=id,
            message=message,
            author_date=author_date,
            committer_date=committer_date,
            author=None,
            committer=None,
            parents=[],
            children=[],
            changes=[],
            branch_id=branch_id,
            repo_size=repo_size,
        )
        # Store IDs temporarily for later linking
        obj._author = author_id
        obj._committer = committer_id
        obj._parents = parent_ids
        obj._children = child_ids
        obj._changes = change_ids

        return obj

    def add_child(self, commit: Commit) -> None:
        self.children = [*self.children, commit]

    def is_after_in_tree(self, other: Commit) -> bool:
        if other in self.parents:
            return True
        return any(parent.is_after_in_tree(other) for parent in self.parents)

    def __str__(self) -> str:
        return self.id

class Change(BaseModel):
    id: str
    commit: Optional[Commit] = None # to not cause errors during loading after serialization
    change_type: ChangeType
    old_file_name: str
    new_file_name: str
    file: Optional[File] = None
    parent_commit: Optional[Commit] = None
    hunks: List[Hunk] = Field(default_factory=list)
    annotated_lines: List[Commit] = Field(default_factory=list)
    parent_change: Optional[Change] = None
    compute_annotated_lines: bool = False

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, values):
        if values.get("id") is None:
            commit = values.get("commit")
            old_name = values.get("old_file_name")
            new_name = values.get("new_file_name")
            if commit and old_name and new_name:
                values["id"] = f"{commit.id}-{old_name}->{new_name}"
        return values

    @property
    def line_changes(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.line_changes]

    @property
    def deleted_lines(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.deleted_lines]

    @property
    def added_lines(self) -> List[LineChange]:
        return [lc for hunk in self.hunks for lc in hunk.added_lines]

    @model_validator(mode="after")
    @classmethod
    def apply_line_changes(cls, model: "Change") -> "Change":
        if model.compute_annotated_lines and not model.file.is_binary:
            model._apply_line_changes(model.parent_change)
        return model

    def __reduce__(self):
        state = (self.id,
                 self.commit.id,
                 self.change_type,
                 self.old_file_name,
                 self.new_file_name,
                 self.file.id,
                 self.parent_commit.id if self.parent_commit else None,
                 self.hunks,
                 [a.id for a in self.annotated_lines],
                 self.parent_change.id if self.parent_change else None,
                 self.compute_annotated_lines)
        return self._rebuild, state

    @classmethod
    def _rebuild(
            cls,
            id: str,
            commit_id: str,
            change_type: ChangeType,
            old_file_name: str,
            new_file_name: str,
            file_id: uuid.UUID,
            parent_commit_id: Optional[str],
            hunks: list,
            annotated_line_ids: List[str],
            parent_change_id: Optional[str],
            compute_annotated_lines: bool,
    ):
        obj = cls(
            id=id,
            commit=None,  # will attach later
            change_type=change_type,
            old_file_name=old_file_name,
            new_file_name=new_file_name,
            file=None,  # will attach later
            parent_commit=None,
            hunks=hunks,
            annotated_lines=[],
            parent_change=None,
            compute_annotated_lines=compute_annotated_lines,
        )
        # Store IDs for later linking
        obj._commit = commit_id
        obj._file = file_id
        obj._parent_commit = parent_commit_id
        obj._annotated_lines = annotated_line_ids
        obj._parent_change = parent_change_id

        return obj

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








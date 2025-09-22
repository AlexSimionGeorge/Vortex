from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from src.common.models import Project
from src.github_miner.linker.registries import GitHubUserRegistry, PullRequestRegistry, GitHubCommitRegistry


from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    url: str
    login: Optional[str]
    name: Optional[str]

    pull_requests_as_creator: List["PullRequest"] = Field(default_factory=list)
    pull_requests_as_merged_by: List["PullRequest"] = Field(default_factory=list)
    pull_requests_as_assignee: List["PullRequest"] = Field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, GitHubUser):
            return False
        return (self.url, self.login, self.name) == (other.url, other.login, other.name)

    def __hash__(self):
        return hash((self.url, self.login, self.name))


class PullRequest(BaseModel):
    number: int
    title: str
    state: str
    changedFiles: int
    body: str
    createdAt: datetime
    mergedAt: Optional[datetime]
    closedAt: Optional[datetime]
    updatedAt: Optional[datetime]

    createdBy: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = Field(default_factory=list)
    mergedBy: Optional[GitHubUser] = None
    git_hub_commits: List["GitHubCommit"] = Field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, PullRequest):
            return False
        return (
            self.number,
            self.title,
            self.state,
            self.changedFiles,
            self.body,
            self.createdAt,
            self.mergedAt,
            self.closedAt,
            self.updatedAt,
        ) == (
            other.number,
            other.title,
            other.state,
            other.changedFiles,
            other.body,
            other.createdAt,
            other.mergedAt,
            other.closedAt,
            other.updatedAt,
        )

    def __hash__(self):
        return hash((
            self.number,
            self.title,
            self.state,
            self.changedFiles,
            self.body,
            self.createdAt,
            self.mergedAt,
            self.closedAt,
            self.updatedAt,
        ))


class GitHubCommit(BaseModel):
    id: str
    date: datetime
    message: str
    changedFiles: int

    pull_requests: List[PullRequest] = Field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, GitHubCommit):
            return False
        return (self.id, self.date, self.message, self.changedFiles) == (
            other.id,
            other.date,
            other.message,
            other.changedFiles,
        )

    def __hash__(self):
        return hash((self.id, self.date, self.message, self.changedFiles))




class GitHubProject(Project):
    name: str
    git_hub_user_registry: GitHubUserRegistry = Field(default_factory=GitHubUserRegistry)
    pull_request_registry: PullRequestRegistry = Field(default_factory=PullRequestRegistry)
    git_hub_commit_registry: GitHubCommitRegistry = Field(default_factory=GitHubCommitRegistry)

    def __str__(self):
        return (
            f"GitHubProject(name={self.name},\n"
            f"git_hub_user_registry: {len(self.git_hub_user_registry.all)},\n"
            f"pull_request_registry: {len(self.pull_request_registry.all)},\n"
            f"git_hub_commit_registry: {len(self.git_hub_commit_registry.all)}\n"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GitHubProject):
            return False
        return (
            self.name == other.name
            and self.git_hub_user_registry._map == other.git_hub_user_registry._map
            and self.pull_request_registry._map  == other.pull_request_registry._map
            and self.git_hub_commit_registry._map  == other.git_hub_commit_registry._map
        )













from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from src.common.models import Project
from src.github_miner.linker.registries import GitHubUserRegistry, PullRequestRegistry, GitHubCommitRegistry


class GitHubUser(BaseModel):
    url: str
    login: Optional[str]
    name: Optional[str]

    pull_requests_as_creator: List[PullRequest] = Field(default_factory=list)
    pull_requests_as_merged_by: List[PullRequest] = Field(default_factory=list)
    pull_requests_as_assignee: List[PullRequest] = Field(default_factory=list)

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
    git_hub_commits: List[GitHubCommit] = Field(default_factory=list)

class GitHubCommit(BaseModel):
    id: str
    date: datetime
    message: str
    changedFiles: int

    pull_requests: List[PullRequest] = Field(default_factory=list)



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













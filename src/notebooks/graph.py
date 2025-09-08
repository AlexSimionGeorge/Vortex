from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Literal, Any, Dict, List, Union, ClassVar, Tuple, Callable, Set
from pydantic import BaseModel, Field
import re
import pickle
from pathlib import Path

from src.github_miner import JsonFileFormatGithub
from src.inspector_git import GitLogDTO
from src.jira_miner.models import JsonFileFormatJira
from typing import Generic, TypeVar, Iterable

T = TypeVar("T")

def get_or_add(items: List[T], obj: T) -> T:
    for existing in items:
        if existing == obj:
            return existing
    items.append(obj)
    return obj


# --------------------
# Node models
# --------------------

class NodeBase(BaseModel, ABC):
    @abstractmethod
    def number_of_connections(self) -> int:
        pass

    def __str__(self):
        return self.model_dump()

class GitCommit(NodeBase):
    sha: str
    message: str
    author_date: datetime
    committer_date: datetime

    committer: Optional[GitUser] = None
    author: Optional[GitUser] = None

    files: List[File] = Field(default_factory=list)

    issues: List[Issue] = Field(default_factory=list)
    pull_requests: List[PullRequest] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
                len(self.files)
                + len(self.issues)
                + len(self.pull_requests)
                + int(self.committer is not None)
                + int(self.author is not None)
        )

    def __hash__(self) -> int:
        return hash(f"GitCommit:{self.sha}")

    def __eq__(self, other):
        if not isinstance(other, GitCommit):
            return False
        return self.sha == other.sha

class GitUser(NodeBase):
    email: str
    name: str

    git_commits_as_committer: List[GitCommit] = Field(default_factory=list)
    git_commits_as_author: List[GitCommit] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
                len(self.git_commits_as_author)
                + len(self.git_commits_as_committer)
        )

    def __hash__(self) -> int:
        return hash(f"GitUser:{self.email}")

    def __eq__(self, other):
        if not isinstance(other, GitUser):
            return False
        return self.email == other.email





class File(NodeBase):
    incremented_number_that_will_solve_all_of_my_problems: int
    path: str
    history: List[Tuple[str, str, str]] = [] # (old_path, new_path, commit_sha)

    git_commits: List[GitCommit] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
                len(self.git_commits)
        )

    def __hash__(self) -> int:
        return hash(f"File:{self.incremented_number_that_will_solve_all_of_my_problems}")

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return self.incremented_number_that_will_solve_all_of_my_problems == other.incremented_number_that_will_solve_all_of_my_problems









class IssueStatusCategory(NodeBase):
    key: str
    name: str

    issue_statuses: List[IssueStatus] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return len(self.issue_statuses)

    def __hash__(self) -> int:
        return hash(f"IssueStatus:{self.key}")

    def __eq__(self, other):
        if not isinstance(other, IssueStatusCategory):
            return False
        return self.key == other.key

class IssueStatus(NodeBase):
    id: str
    name: str

    issue_status_categories: IssueStatusCategory = Field(default_factory=IssueStatusCategory)
    issues: List[Issue] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return len(self.issues) + 1 # 1 for the link with category

    def __hash__(self) -> int:
        return hash(f"IssueStatus:{self.id}")

    def __eq__(self, other):
        if not isinstance(other, IssueStatus):
            return False
        return self.id == other.id

class IssueType(NodeBase):
    id: str
    name: str
    description: str
    isSubTask: bool

    issues: List[Issue] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return len(self.issues)

    def __hash__(self) -> int:
        return hash(f"IssueType:{self.id}")

    def __eq__(self, other):
        if not isinstance(other, IssueType):
            return False
        return self.id == other.id

class Issue(NodeBase):
    id: int
    key: str
    summary: str
    createdAt: datetime
    updatedAt: datetime

    issue_statuses: List[IssueStatus] = Field(default_factory=list)
    issue_types: List[IssueType] = Field(default_factory=list)
    creator: Optional[JiraUser] = None
    jira_users_as_assignee: List[JiraUser] = Field(default_factory=list)
    reporter: Optional[JiraUser] = None
    parent:Optional[Issue] = None
    children:List[Issue] = Field(default_factory=list)

    git_commits: List[GitCommit] = Field(default_factory=list)
    pull_requests: List[PullRequest] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
            len(self.issue_statuses) +
            len(self.issue_types) +
            int(self.creator is not None) +
            len(self.jira_users_as_assignee)+
            int(self.reporter is not None) +
            int(self.parent is not None) +
            len(self.children) +
            len(self.git_commits) +
            len(self.pull_requests)
        )

    def __hash__(self) -> int:
        return hash(f"Issue:{self.key}")

    def __eq__(self, other):
        if not isinstance(other, Issue):
            return False
        return self.key == other.key

class JiraUser(NodeBase):
    key: str
    name: str
    link: str

    issues_as_reporter: List[Issue] = Field(default_factory=list)
    issues_as_creator: List[Issue] = Field(default_factory=list)
    issues_as_assignee: List[Issue] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
            len(self.issues_as_reporter) +
            len(self.issues_as_creator) +
            len(self.issues_as_assignee)
        )

    def __hash__(self) -> int:
        return hash(f"JiraUser:{self.key}")

    def __eq__(self, other):
        if not isinstance(other, JiraUser):
            return False
        return self.key == other.key

class GitHubUser(NodeBase):
    url: str
    login: Optional[str]
    name: Optional[str]

    pull_requests_as_creator: List[PullRequest] = Field(default_factory=list)
    pull_requests_as_merged_by: List[PullRequest] = Field(default_factory=list)
    pull_requests_as_assignee: List[PullRequest] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
            len(self.pull_requests_as_creator) +
            len(self.pull_requests_as_merged_by) +
            len(self.pull_requests_as_assignee)
        )

    def __hash__(self) -> int:
        return hash(f"GitHubUser:{self.url}")

    def __eq__(self, other):
        if not isinstance(other, GitHubUser):
            return False
        return self.url == other.url

class PullRequest(NodeBase):
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

    issues: List[Issue] = Field(default_factory=list)
    git_commits: List[GitCommit] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
            int(self.createdBy is not None) +
            len(self.assignees) +
            int(self.mergedBy is not None) +
            len(self.git_hub_commits) +
            len(self.issues) +
            len(self.git_commits)
        )

    def __hash__(self) -> int:
        return hash(f"PullRequest:{self.number}")

    def __eq__(self, other):
        if not isinstance(other, PullRequest):
            return False
        return self.number == other.number

class GitHubCommit(NodeBase):
    sha: str
    date: datetime
    message: str
    changedFiles: int

    pull_requests: List[PullRequest] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        return (
            len(self.pull_requests)
        )

    def __hash__(self) -> int:
        return hash(f"GitHubCommit:{self.sha}")

    def __eq__(self, other):
        if not isinstance(other, GitHubCommit):
            return False
        return self.sha == other.sha

class Graph(BaseModel):
    # Nodes
    # inspector git
    git_commits: List[GitCommit] = Field(default_factory=list)
    git_users: List[GitUser] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)

    # jira
    issue_status_categories: List[IssueStatusCategory] = Field(default_factory=list)
    issue_statuses: List[IssueStatus] = Field(default_factory=list)
    issue_types: List[IssueType] = Field(default_factory=list)
    jira_users: List[JiraUser] = Field(default_factory=list)
    issues: List[Issue] = Field(default_factory=list)

    # github
    pull_requests: List[PullRequest] = Field(default_factory=list)
    git_hub_users: List[GitHubUser] = Field(default_factory=list)
    git_hub_commits: List[GitHubCommit] = Field(default_factory=list)

    def number_of_connections(self) -> int:
        nr_con = 0
        for node in self.git_commits:
            nr_con += node.number_of_connections()
        for node in self.git_users:
            nr_con += node.number_of_connections()
        for node in self.files:
            nr_con += node.number_of_connections()

        for node in self.issue_status_categories:
            nr_con += node.number_of_connections()
        for node in self.issue_statuses:
            nr_con += node.number_of_connections()
        for node in self.issue_types:
            nr_con += node.number_of_connections()
        for node in self.jira_users:
            nr_con += node.number_of_connections()
        for node in self.issues:
            nr_con += node.number_of_connections()

        for node in self.pull_requests:
            nr_con += node.number_of_connections()
        for node in self.git_hub_users:
            nr_con += node.number_of_connections()
        for node in self.git_hub_commits:
            nr_con += node.number_of_connections()

        return nr_con

    def number_of_nodes(self) -> int:
        return (
                len(self.git_commits) +
                len(self.git_users) +
                len(self.files) +

                len(self.issue_statuses) +
                len(self.issue_types) +
                len(self.issue_status_categories) +
                len(self.jira_users) +
                len(self.issues) +

                len(self.pull_requests) +
                len(self.git_hub_users) +
                len(self.git_hub_commits)
        )

    def add_commit(self, commit: GitCommit) -> GitCommit:
        return get_or_add(self.git_commits, commit)

    def get_git_commit(self, sha: str) -> GitCommit | None:
        return next((c for c in self.git_commits if c.sha == sha), None)

    def add_git_user(self, user: GitUser) -> GitUser:
        return get_or_add(self.git_users, user)

    def add_file(self, file: File) -> None:
        self.files.append(file)

    def add_issue_status(self, issue_status: IssueStatus) -> IssueStatus:
        return get_or_add(self.issue_statuses, issue_status)

    def get_issue_status(self, id:str) -> IssueStatus:
        return next((s for s in self.issue_statuses if s.id == id), None)

    def add_issue_type(self, issue_type: IssueType) -> IssueType:
        return get_or_add(self.issue_types, issue_type)

    def get_issue_type(self, name:str) -> IssueType | None:
        return next((t for t in self.issue_types if t.name == name), None)

    def add_issue_status_category(self, issue_status_category: IssueStatusCategory) -> IssueStatusCategory:
        return get_or_add(self.issue_status_categories, issue_status_category)

    def add_jira_user(self, user: JiraUser) -> JiraUser:
        return get_or_add(self.jira_users, user)

    def get_jira_user(self, link:str) -> JiraUser | None:
        return next((u for u in self.jira_users if u.link == link), None)

    def add_issue(self, issue: Issue) -> Issue:
        return get_or_add(self.issues, issue)

    def get_issue(self, key:str) -> Issue:
        return next((i for i in self.issues if i.key == key), None)

    def add_pull_request(self, pull_request: PullRequest) -> PullRequest:
        return get_or_add(self.pull_requests, pull_request)

    def get_pull_request(self, number:int) -> PullRequest:
        return next ((p for p in self.pull_requests if p.number == number), None)

    def add_git_hub_user(self, git_hub_user: GitHubUser) -> GitHubUser:
        return get_or_add(self.git_hub_users, git_hub_user)

    def add_git_hub_commit(self, git_hub_commit: GitHubCommit) -> GitHubCommit:
        return get_or_add(self.git_hub_commits, git_hub_commit)

    def summary(self) -> str:
        return (
            f"~~~~ Graph summary ~~~~\n"
            f"commits: {len(self.git_commits)}\n"
            f"git_users: {len(self.git_users)}\n"
            f"files: {len(self.files)}\n"
            "\n"
            f"issue_statuses: {len(self.issue_statuses)}\n"
            f"issue_types: {len(self.issue_types)}\n"
            f"issue_status_categories: {len(self.issue_status_categories)}\n"
            f"jira_users: {len(self.jira_users)}\n"
            f"issues: {len(self.issues)}\n"
            "\n"
            f"pull_requests: {len(self.pull_requests)}\n"
            f"git_hub_users: {len(self.git_hub_users)}\n"
            f"git_hub_commits: {len(self.git_hub_commits)}\n"
            "\n"
            f"nodes: {self.number_of_nodes()}\n"
            f"edges: {self.number_of_connections()}\n"
        )

    def __repr__(self) -> str:
        return self.summary()

    def __str__(self) -> str:
        return self.summary()

    def add_inspector_git_data(self, inspector_git_data: GitLogDTO, indexing:int = 1):
        git_date_format = "%a %b %d %H:%M:%S %Y %z"
        #commits are sorted by commiter date
        for commitDTO in inspector_git_data.commits:
            # Create commit object
            commit = GitCommit(
                sha=commitDTO.id,
                message=commitDTO.message,
                author_date=datetime.strptime(commitDTO.author_date, git_date_format),
                committer_date=datetime.strptime(commitDTO.committer_date, git_date_format)
            )
            commit = self.add_commit(commit)

            # Create author and committer objects
            author = GitUser(email=commitDTO.author_email, name=commitDTO.author_name)
            committer = GitUser(email=commitDTO.committer_email, name=commitDTO.committer_name)
            author = self.add_git_user(author)
            committer = self.add_git_user(committer)

            # Link commit to author and committer
            commit.author = author
            commit.committer = committer
            get_or_add(author.git_commits_as_author, commit)
            get_or_add(committer.git_commits_as_committer, commit)



        def find_file(old_path, new_path, current_commit_sha, indexing):
            f = next((f for f in self.files if f.path == old_path), None)
            if f:
                if old_path != new_path:
                    f.history.append((old_path, new_path, current_commit_sha))
                    f.path = new_path
                return f, indexing

            for f in self.files:
                for h in f.history:
                    if h[1] == new_path:
                        return f, indexing

            for cdto in inspector_git_data.commits:
                for ch in cdto.changes:
                    if ch.new_file_name == old_path: # daca gasesti un change care lasa fisierul cu numele pe care il caut
                        if ch.old_file_name != ch.new_file_name: # daca changeul este cel care schimba numele fisierului
                            my_tuple = (ch.old_file_name, ch.new_file_name, cdto.id)
                            f = File(path=new_path,
                                     incremented_number_that_will_solve_all_of_my_problems=indexing)
                            indexing += 1
                            f.history.append(my_tuple)
                            f.history.append((old_path, new_path, current_commit_sha))
                            self.add_file(f)
                            return f, indexing

            return None, indexing

        for commitDTO in inspector_git_data.commits:
            commit = self.get_git_commit(commitDTO.id)

            # Process changes (files)
            for change in commitDTO.changes:
                if change.old_file_name == "/dev/null":
                    file = File(path=change.new_file_name
                                , incremented_number_that_will_solve_all_of_my_problems=indexing)
                    indexing += 1
                    file.history.append((change.old_file_name, change.new_file_name, commitDTO.id))
                    self.add_file(file)
                else:
                    file, indexing = find_file(change.old_file_name, change.new_file_name, commitDTO.id, indexing)


                get_or_add(commit.files, file)
                get_or_add(file.git_commits, commit)

        print(f"Indexing is {indexing}")




    def add_jira_data(self, jira_data: JsonFileFormatJira):
        def add_issue_statuses():
            for status in jira_data.issueStatuses:
                category = IssueStatusCategory(
                    key=status.statusCategory.key,
                    name=status.statusCategory.name
                )
                issue_status = IssueStatus(
                    id=status.id,
                    name=status.name,
                    issue_status_categories = category,
                )

                category = self.add_issue_status_category(category)
                issue_status = self.add_issue_status(issue_status)

                get_or_add(category.issue_statuses, issue_status)

        def add_issue_types():
            for issue_type in jira_data.issueTypes:
                it = IssueType(
                    id=issue_type.id,
                    name=issue_type.name,
                    description=issue_type.description,
                    isSubTask=issue_type.isSubTask,
                )
                self.add_issue_type(it)

        def add_users():
            for user in jira_data.users:
                jira_user = JiraUser(
                    key=user.key,
                    name=user.name,
                    link=user.self_,
                )
                self.add_jira_user(jira_user)

        def add_issues():
            for issue in jira_data.issues:
                i = Issue(
                    id=issue.id,
                    key=issue.key,
                    summary=issue.summary,
                    createdAt=issue.created,
                    updatedAt=issue.updated,
                )
                i = self.add_issue(i)


                # Resolve status
                issue_status = self.get_issue_status(issue.status.id)
                get_or_add(issue_status.issues, i)
                get_or_add(i.issue_statuses, issue_status)

                # Resolve type
                issue_type = self.get_issue_type(issue.issueType)
                get_or_add(issue_type.issues, i)
                get_or_add(i.issue_types, issue_type)

                # Resolve reporter
                reporter = self.get_jira_user(issue.reporterId)
                get_or_add(reporter.issues_as_reporter, i)
                i.reporter = reporter

                # Resolve creator
                if issue.creatorId is not None:
                    creator = self.get_jira_user(issue.creatorId)
                    get_or_add(creator.issues_as_creator, i)
                    i.creator = creator


                # Resolve assignee
                if issue.assigneeId is not None:
                    assignee = self.get_jira_user(issue.assigneeId)
                    get_or_add(assignee.issues_as_assignee, i)
                    get_or_add(i.jira_users_as_assignee, assignee)

        def make_issue_parent_connections():
            for jira_issue in jira_data.issues:
                current_issue = self.get_issue(jira_issue.key)
                if not current_issue:
                    print(f"Issue {jira_issue.key} not found in graph")
                    continue

                if jira_issue.parent is not None:
                    parent_issue = self.get_issue(jira_issue.parent)
                    current_issue.parent = parent_issue
                    get_or_add(parent_issue.children, current_issue)

        # Run the inner helper functions
        add_issue_statuses()
        add_issue_types()
        add_users()
        add_issues()
        make_issue_parent_connections()

    def add_github_data(self, github_data: JsonFileFormatGithub):
        for pr in github_data.pullRequests:
            # ADD PR
            pull_request = PullRequest(
                number=pr.number,
                title=pr.title,
                state=pr.state,
                changedFiles=pr.changedFiles,
                createdAt=pr.createdAt,
                updatedAt=pr.updatedAt,
                body=pr.body,
                mergedAt=pr.mergedAt,
                closedAt=pr.closedAt,
            )
            pull_request = self.add_pull_request(pull_request)

            # ADD ALL USERS (assignees)
            for assignee in pr.assignees:
                assignee_git_hub_user = GitHubUser(
                    url=assignee.url,
                    login=assignee.login,
                    name=assignee.name,
                )
                assignee_git_hub_user = self.add_git_hub_user(assignee_git_hub_user)

                get_or_add(pull_request.assignees, assignee_git_hub_user)
                get_or_add(assignee_git_hub_user.pull_requests_as_assignee, pull_request)

            # ADD CREATOR
            if pr.createdBy:
                creator_git_hub_user = GitHubUser(
                    url=pr.createdBy.url,
                    login=pr.createdBy.login,
                    name=pr.createdBy.name,
                )
                creator_git_hub_user = self.add_git_hub_user(creator_git_hub_user)

                pull_request.createdBy = creator_git_hub_user
                get_or_add(creator_git_hub_user.pull_requests_as_creator, pull_request)

            # ADD MERGER
            if pr.mergedBy:
                merger_git_hub_user = GitHubUser(
                    name=pr.mergedBy.name,
                    url=pr.mergedBy.url,
                    login=pr.mergedBy.login,
                )
                merger_git_hub_user = self.add_git_hub_user(merger_git_hub_user)

                pull_request.mergedBy = merger_git_hub_user
                get_or_add(merger_git_hub_user.pull_requests_as_merged_by, pull_request)

            # ADD ALL COMMITS
            for c in pr.commits:
                commit = GitHubCommit(
                    sha=c.sha,
                    date=c.date,
                    message=c.message,
                    changedFiles=c.changedFiles,
                )
                commit = self.add_git_hub_commit(commit)

                get_or_add(pull_request.git_hub_commits, commit)
                get_or_add(commit.pull_requests, pull_request)

    def link_issues_with_git_commits(self):
        issue_keys = [re.escape(issue.key) for issue in self.issues]
        issue_pattern = re.compile(r'\b(' + '|'.join(issue_keys) + r')\b', re.IGNORECASE)

        links = 0
        commits_liked_with_issues = 0

        for commit in self.git_commits:
            if not commit.message:
                continue

            matches = issue_pattern.findall(commit.message)

            if len(matches) > 0:
                commits_liked_with_issues += 1

            for match in set(matches):
                issue = self.get_issue(match.upper())
                get_or_add(issue.git_commits, commit)
                get_or_add(commit.issues, issue)
                links += 1

        # print(f"There are {links} Issue–Commit edges")
        # print(f"Commits liked with issues: {commits_liked_with_issues}")

    def link_pull_request_with_issue(self, jira_data: JsonFileFormatJira):
        # Build one regex for all issue keys
        issue_keys = [re.escape(issue.key) for issue in self.issues]
        issue_pattern = re.compile(r'\b(' + '|'.join(issue_keys) + r')\b', re.IGNORECASE)

        links = 0
        prs_with_issues = 0

        for pr in self.pull_requests:
            text = (pr.title or "") + " " + (pr.body or "")
            matches = issue_pattern.findall(text)

            if matches:
                prs_with_issues += 1
            for match in set(matches):
                issue = self.get_issue(match.upper())
                if issue:
                    get_or_add(pr.issues, issue)
                    get_or_add(issue.pull_requests, pr)
                    links += 1

        # print(f"Created {links} PR–Issue edges")
        # print(f"PRs linked with issues: {prs_with_issues}")

        def extract_pr_number(text: str) -> int | None:
            match = re.search(r'#(\d+)', text)
            if match:
                return int(match.group(1))
            return None

        for issue in jira_data.issues:
            issues_pr_links = set()
            for change in issue.changes:
                for item in change.items:
                    if item.toString and "Pull Request #" in item.toString:
                        issues_pr_links.add(item.toString)
            if len(issues_pr_links) > 0:
                i = self.get_issue(issue.key)
                for link in issues_pr_links:
                    pr = self.get_pull_request(extract_pr_number(link))
                    if not pr:
                        # print(f"Unknown reference in {i.key} of a pull request: {link}")
                        continue

                    get_or_add(pr.issues, i)
                    get_or_add(i.pull_requests, pr)

    def link_pull_requests_with_git_commits(self):
        direct_links = 0
        linked_via_issue = 0

        for pr in self.pull_requests:
            # 1. Exact SHA match for commits
            for pr_commit in pr.git_hub_commits:
                git_commit = self.get_git_commit(pr_commit.sha)
                if git_commit:
                    get_or_add(git_commit.pull_requests, pr)
                    get_or_add(pr.git_commits, git_commit)
                    direct_links += 1

            # 2. Fallback: link via issues associated with PR
            for issue in pr.issues:
                for git_commit in issue.git_commits:
                    get_or_add(git_commit.pull_requests, pr)
                    get_or_add(pr.git_commits, git_commit)
                    linked_via_issue += 1

        # print(f"Direct links: {direct_links}")
        # print(f"Linked via issues: {linked_via_issue}")

    def save(self, path: str | Path = None):
        """
        Save the Graph object using pickle.

        Args:
            path: Optional path to save the pickle file. If None, defaults to "pickle_data/graph.pkl".

        Returns:
            Path to the saved pickle file.
        """
        # Default path if none provided
        if path is None:
            base_dir = Path("pickle_data")
            base_dir.mkdir(parents=True, exist_ok=True)
            pickle_path = base_dir / "graph.pkl"
        else:
            pickle_path = Path(path)
            pickle_path.parent.mkdir(parents=True, exist_ok=True)

        # Save self
        with open(pickle_path, "wb") as f:
            pickle.dump(self, f)

        print(f"Saved Graph to {pickle_path}")
        return pickle_path

    @classmethod
    def load(cls, path: str | Path = None):
        """
        Load a Graph object from a pickle file.

        Args:
            path: Optional path to the pickle file. If None, defaults to "pickle_data/graph.pkl".

        Returns:
            A Graph instance loaded from the pickle.
        """
        if path is None:
            pickle_path = Path("pickle_data/graph.pkl")
        else:
            pickle_path = Path(path)

        if not pickle_path.exists():
            raise FileNotFoundError(f"No pickle file found at {pickle_path}")

        with open(pickle_path, "rb") as f:
            obj = pickle.load(f)

        if not isinstance(obj, cls):
            raise TypeError(f"Loaded object is not a {cls.__name__} instance")

        print(f"Loaded Graph from {pickle_path}")
        return obj

__all__ = [
    "NodeBase", "GitCommit", "GitUser", "File", "IssueStatus", "IssueStatusCategory",
    "IssueType", "Graph", "JiraUser", "Issue", "GitHubUser", "GitHubCommit",
    "PullRequest"
]




from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Literal, Any, Dict, List, Union, ClassVar, Tuple, Callable
from pydantic import BaseModel, Field


# --------------------
# Node models
# --------------------

class NodeBase(BaseModel, ABC):
    @abstractmethod
    def dict_key(self) -> str:
        """Returns a uniques representation for this node."""
        pass

    def __str__(self):
        return self.model_dump()

class GitCommit(NodeBase):
    sha: str
    message: str
    author_date: datetime
    committer_date: datetime

    def dict_key(self) -> str:
        return f"GitCommit:{self.sha}"

class GitUser(NodeBase):
    email: str
    name: str

    def dict_key(self) -> str:
        return f"GitUser:{self.email}"

class File(NodeBase):
    path: str

    def dict_key(self) -> str:
        return f"File:{self.path}"

class IssueStatusCategory(NodeBase):
    key: str
    name: str

    def dict_key(self) -> str:
        return f"IssueStatus:{self.key}"

class IssueStatus(NodeBase):
    id: str
    name: str

    def dict_key(self) -> str:
        return f"IssueStatus:{self.id}"

class IssueType(NodeBase):
    id: str
    name: str
    description: str
    isSubTask: bool

    def dict_key(self) -> str:
        return f"IssueType:{self.id}"

class Issue(NodeBase):
    id: int
    key: str
    summary: str
    createdAt: datetime
    updatedAt: datetime

    def dict_key(self) -> str:
        return f"Issue:{self.key}"

class JiraUser(NodeBase):
    key: str
    name: str
    link: str
    def dict_key(self) -> str:
        return f"JiraUser:{self.key}"

class GitHubUser(NodeBase):
    url: str
    login: Optional[str]
    name: Optional[str]


    def dict_key(self) -> str:
        return f"GitHubUser:{self.url}"

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

    def dict_key(self) -> str:
        return f"PullRequest:{self.number}"

class GitHubCommit(NodeBase):
    sha: str
    date: datetime
    message: str
    changedFiles: int

    def dict_key(self) -> str:
        return f"GitHubCommit:{self.sha}"

# --------------------
# Edge models
# --------------------

class EdgeBase(BaseModel, ABC):
    node_type_map: ClassVar[Dict[str, str]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.node_type_map is None:
            raise TypeError(f"{cls.__name__} must define `node_type_map`")

    @abstractmethod
    def get_nodes_identifier(self) -> List[str]:
        """Return a list of node identifiers involved in this edge."""
        pass

    def edge_type_for_node(self, node_key: str) -> str:
        """Return the type of the node connected to `node_key` in this edge."""
        for prefix, edge_type in self.node_type_map.items():
            if node_key.startswith(prefix):
                return edge_type
        raise ValueError(f"Node key {node_key} not in this edge")

    def other_node(self, node_key: str):
        """Return the actual neighbor node object given one node key."""
        # get the field that corresponds to that key
        for field_name, value in self.__dict__.items():
            if hasattr(value, "dict_key") and value.dict_key() == node_key:
                # find the other field
                for f2, v2 in self.__dict__.items():
                    if f2 != field_name and hasattr(v2, "dict_key"):
                        return v2
        raise ValueError(f"Node {node_key} not found in this edge {self}")

    def __str__(self):
        return self.model_dump()

class GitCommitGitUserEdge(EdgeBase):
    commit: GitCommit
    git_user: GitUser
    role: Literal["author", "committer"]

    node_type_map = {
        "GitCommit:": "git_users",
        "GitUser:": "git_commits",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.commit.dict_key(),self.git_user.dict_key()]

class GitCommitFileEdge(EdgeBase):
    commit: GitCommit
    file: File
    change_type: Optional[Any] = None

    node_type_map = {
        "GitCommit:": "files",
        "File:": "git_commits",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.commit.dict_key(),self.file.dict_key()]

class GitUserFileEdge(EdgeBase):
    git_user: GitUser
    file: File
    role: Literal["writer", "reviewer"]

    node_type_map = {
        "GitUser:": "files",
        "File:": "git_users",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.git_user.dict_key() ,self.file.dict_key()]

class IssueStatusIssueStatusCategoryEdge(EdgeBase):
    issue_status: IssueStatus
    issue_status_category: IssueStatusCategory

    node_type_map = {
        "IssueStatus:": "issue_status_categories",
        "IssueStatusCategory:": "issue_statuses",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.issue_status.dict_key(),self.issue_status_category.dict_key()]

class IssueIssueStatusEdge(EdgeBase):
    issue_status: IssueStatus
    issue: Issue

    node_type_map = {
        "IssueStatus:": "issues",
        "Issue": "issue_statuses",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.issue_status.dict_key(),self.issue.dict_key()]

class IssueIssueTypeEdge(EdgeBase):
    issue_type: IssueType
    issue: Issue

    node_type_map = {
        "IssueType:": "issues",
        "Issue:": "issue_types",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.issue_type.dict_key(),self.issue.dict_key()]

class IssueJiraUserEdge(EdgeBase):
    issue: Issue
    jira_user: JiraUser
    role: Literal["assignee", "reporter", "creator"]

    node_type_map = {
        "Issue:": "users",
        "JiraUser:": "issues",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.jira_user.dict_key(),self.jira_user.dict_key()]

class IssueIssueEdge(EdgeBase):
    child: Issue
    parent: Issue

    node_type_map = {"Issue:": "issues",}

    def get_nodes_identifier(self) -> List[str]:
        return [self.child.dict_key(),self.parent.dict_key()]

    def normalized_key(self) -> frozenset:
        """Return a unique, order-independent key for this edge."""
        return frozenset(self.get_nodes_identifier())

class PullRequestGitHubUserEdge(EdgeBase):
    pr: PullRequest
    git_hub_user: GitHubUser
    role: Literal["creator", "assignee", "merger"]

    node_type_map = {
        "PullRequest:": "git_hub_users",
        "GitHubUser:": "pull_requests",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.git_hub_user.dict_key(),self.pr.dict_key()]

class PullRequestGitHubCommitEdge(EdgeBase):
    pr: PullRequest
    commit: GitHubCommit
    node_type_map = {
        "PullRequest:": "git_hub_commits",
        "GitHubCommit:": "pull_requests",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.commit.dict_key(),self.pr.dict_key()]

class GitCommitIssueEdge(EdgeBase):
    git_commit: GitCommit
    issue: Issue

    node_type_map = {
        "Issue:": "git_commits",
        "GitCommit:": "issues",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.git_commit.dict_key(),self.issue.dict_key()]

class PullRequestIssueEdge(EdgeBase):
    pr: PullRequest
    issue: Issue

    node_type_map = {
        "Issue:": "pull_requests",
        "PullRequest:": "issues",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.issue.dict_key(),self.pr.dict_key()]

class GitCommitPullRequestEdge(EdgeBase):
    git_commit: GitCommit
    pr: PullRequest
    relation: Literal["merged_as", "contains_commit", "linked_via_issue"]

    node_type_map = {
        "PullRequest:": "git_commits",
        "GitCommit:": "pull_requests",
    }

    def get_nodes_identifier(self) -> List[str]:
        return [self.git_commit.dict_key(), self.pr.dict_key()]

    def edge_key(self) -> str:
        """
        Returns a unique string representing this edge,
        based on git_commit, PR, and relation.
        """
        return f"{self.git_commit.dict_key()}->{self.pr.dict_key()}|{self.relation}"

    def __hash__(self):
        return hash(self.edge_key())

    def __eq__(self, other):
        if not isinstance(other, GitCommitPullRequestEdge):
            return False
        return self.edge_key() == other.edge_key()

class Graph(BaseModel):
    # Nodes
    # inspector git
    commits: Dict[str, GitCommit] = Field(default_factory=dict)
    users_git: Dict[str, GitUser] = Field(default_factory=dict)
    files: Dict[str, File] = Field(default_factory=dict)

    # jira
    issue_status_categories: Dict[str, IssueStatusCategory] = Field(default_factory=dict)
    issue_statuses: Dict[str, IssueStatus] = Field(default_factory=dict)
    issue_types: Dict[str, IssueType] = Field(default_factory=dict)
    users_jira: Dict[str, JiraUser] = Field(default_factory=dict)
    issues: Dict[str, Issue] = Field(default_factory=dict)

    # github
    pull_requests: Dict[str, PullRequest] = Field(default_factory=dict)
    git_hub_users: Dict[str, GitHubUser] = Field(default_factory=dict)
    git_hub_commits: Dict[str, GitHubCommit] = Field(default_factory=dict)

    # Edges
    edges: List[EdgeBase] = Field(default_factory=list)

    # Adjacency maps for fast traversal
    adjacency: Dict[str, Dict[str, List[EdgeBase]]] = Field(default_factory=dict)

    def add_commit(self, commit: GitCommit) -> None:
        self.commits[commit.dict_key()] = commit

    def add_user_git(self, user: GitUser) -> None:
        self.users_git[user.dict_key()] = user

    def add_file(self, file: File, old_name: str | None = None) -> None:
        if old_name and old_name in self.files:
            old_file = File(path=old_name)
            del self.files[old_file.dict_key()]
        self.files[file.dict_key()] = file

    def add_issue_status(self, issue_status: IssueStatus) -> None:
        self.issue_statuses[issue_status.dict_key()] = issue_status

    def get_issue_status(self, id:str) -> IssueStatus:
        return self.issue_statuses[f"IssueStatus:{id}"]

    def add_issue_type(self, issue_type: IssueType) -> None:
        self.issue_types[issue_type.dict_key()] = issue_type

    def get_issue_type(self, name:str) -> IssueType | None:
        for issue_type in self.issue_types.values():
            if name == issue_type.name:
                return issue_type
        return None

    def add_issue_status_category(self, issue_status_category: IssueStatusCategory) -> None:
        self.issue_status_categories[issue_status_category.dict_key()] = issue_status_category

    def add_jira_user(self, user: JiraUser) -> None:
        self.users_jira[user.dict_key()] = user

    def get_jira_user(self, link:str) -> JiraUser | None:
        for user in self.users_jira.values():
            if link == user.link:
                return user
        return None

    def add_issue(self, issue: Issue) -> None:
        self.issues[issue.dict_key()] = issue

    def get_issue(self, key:str) -> Issue:
        return self.issues[f"Issue:{key}"]

    def add_pull_request(self, pull_request: PullRequest) -> None:
        self.pull_requests[pull_request.dict_key()] = pull_request

    def add_git_hub_user(self, git_hub_user: GitHubUser) -> None:
        self.git_hub_users[git_hub_user.dict_key()] = git_hub_user

    def add_git_hub_commit(self, git_hub_commit: GitHubCommit) -> None:
        self.git_hub_commits[git_hub_commit.dict_key()] = git_hub_commit

    def add_edge(self, edge) -> None:
        self.edges.append(edge)

        identifiers = edge.get_nodes_identifier()

        for node_key_representation in identifiers:
            # figure out which "bucket" this edge belongs to for this node
            edge_type = edge.edge_type_for_node(node_key_representation)
            # ensure the node exists in adjacency
            if node_key_representation not in self.adjacency:
                self.adjacency[node_key_representation] = {}
            # ensure the edge_type list exists
            if edge_type not in self.adjacency[node_key_representation]:
                self.adjacency[node_key_representation][edge_type] = []

            # add the edge
            self.adjacency[node_key_representation][edge_type].append(edge)

    def filtered_traversal(
            self,
            start_nodes: List[NodeBase],
            steps: List[Tuple[str, Optional[Callable[[NodeBase], bool]]]]
    ) -> List[NodeBase]:
        """
        Generalized bucket-based traversal with predicates.

        Args:
            start_nodes (List[NodeBase]): node objects to start from.
            steps (List[Tuple[str, Optional[Callable]]]): list of (bucket, predicate) tuples.
                - bucket (str): which adjacency bucket to follow.
                - predicate (Callable[[NodeBase], bool]): filter function for nodes at that step.

        Returns:
            List[NodeBase]: node objects that satisfy the traversal.
        """

        current_nodes: List[NodeBase] = start_nodes

        for bucket, predicate in steps:
            next_keys: List[NodeBase] = []
            for current_node in current_nodes:
                edges = self.adjacency.get(current_node.dict_key(), {}).get(bucket, [])
                for edge in edges:
                    neighbor = edge.other_node(current_node.dict_key())
                    if neighbor and (predicate is None or predicate(neighbor)):
                        next_keys.append(neighbor)
            current_nodes = next_keys

        return [k for k in current_nodes]

    def summary(self) -> str:
        return (
            f"~~~~ Graph summary ~~~~\n"
            f"commits: {len(self.commits)}\n"
            f"git_users: {len(self.users_git)}\n"
            f"files: {len(self.files)}\n"
            "\n"
            f"issue_statuses: {len(self.issue_statuses)}\n"
            f"issue_types: {len(self.issue_types)}\n"
            f"issue_status_categories: {len(self.issue_status_categories)}\n"
            f"jira_users: {len(self.users_jira)}\n"
            f"issues: {len(self.issues)}\n"
            "\n"
            f"pull_requests: {len(self.pull_requests)}\n"
            f"git_hub_users: {len(self.git_hub_users)}\n"
            f"git_hub_commits: {len(self.git_hub_commits)}\n"
            "\n"
            f"edges: {len(self.edges)}"
        )

    def __repr__(self) -> str:
        return self.summary()

    def __str__(self) -> str:
        return self.summary()


__all__ = [
    "NodeBase", "GitCommit", "GitUser", "File", "IssueStatus", "IssueStatusCategory",
    "IssueType", "EdgeBase", "GitCommitGitUserEdge", "GitCommitFileEdge", "GitUserFileEdge",
    "IssueStatusIssueStatusCategoryEdge", "Graph", "JiraUser", "Issue", "IssueIssueStatusEdge",
    "IssueIssueTypeEdge", "IssueJiraUserEdge", "IssueIssueEdge", "GitHubUser", "GitHubCommit",
    "PullRequest", "PullRequestGitHubUserEdge", "PullRequestGitHubCommitEdge",
    "GitCommitIssueEdge", "PullRequestIssueEdge", "GitCommitPullRequestEdge"
]


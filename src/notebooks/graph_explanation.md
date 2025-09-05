# 📘 Project Graph Overview

This project uses a **graph data model** to connect Git, GitHub, and Jira entities.
The graph consists of:

1. **Nodes** → entities like commits, users, files, issues, etc.
2. **Edges** → typed relationships between nodes (e.g., “commit authored by user”).
3. **Adjacency dictionary** → the main lookup structure to traverse the graph quickly.

---

## 1. Nodes (Entities)

Each node has a unique key (`dict_key()`) used for indexing in the graph.
Here are the main node types:

| Node Type               | Fields (important ones)                                | Unique Key Format      |
| ----------------------- | ------------------------------------------------------ | ---------------------- |
| **GitCommit**           | `sha`, `message`, `author_date`, `committer_date`      | `GitCommit:{sha}`      |
| **GitUser**             | `email`, `name`                                        | `GitUser:{email}`      |
| **File**                | `path`                                                 | `File:{path}`          |
| **Issue**               | `id`, `key`, `summary`, `createdAt`, `updatedAt`       | `Issue:{key}`          |
| **IssueStatus**         | `id`, `name`                                           | `IssueStatus:{id}`     |
| **IssueStatusCategory** | `key`, `name`                                          | `IssueStatus:{key}`    |
| **IssueType**           | `id`, `name`, `description`, `isSubTask`               | `IssueType:{id}`       |
| **JiraUser**            | `key`, `name`, `link`                                  | `JiraUser:{key}`       |
| **GitHubUser**          | `url`, `login`, `name`                                 | `GitHubUser:{url}`     |
| **PullRequest**         | `number`, `title`, `state`, `changedFiles`, timestamps | `PullRequest:{number}` |
| **GitHubCommit**        | `sha`, `message`, `changedFiles`, `date`               | `GitHubCommit:{sha}`   |

---

## 2. Edges (Relationships)

Edges connect **two nodes** and declare the **type of relation**.
They also define a `node_type_map` telling us *what bucket the other node goes into*.

Here’s the complete list:

### Git edges

* **Commit ↔ User** (`GitCommitGitUserEdge`)

  * `"GitCommit:" → "git_users"`
  * `"GitUser:" → "git_commits"`
  * Role: `author` or `committer`

* **Commit ↔ File** (`GitCommitFileEdge`)

  * `"GitCommit:" → "files"`
  * `"File:" → "git_commits"`
  * Extra: `change_type` (optional)

* **User ↔ File** (`GitUserFileEdge`)

  * `"GitUser:" → "files"`
  * `"File:" → "git_users"`
  * Role: `writer` or `reviewer`

### Jira edges

* **IssueStatus ↔ IssueStatusCategory** (`IssueStatusIssueStatusCategoryEdge`)

  * `"IssueStatus:" → "issue_status_categories"`
  * `"IssueStatusCategory:" → "issue_statuses"`

* **Issue ↔ IssueStatus** (`IssueIssueStatusEdge`)

  * `"IssueStatus:" → "issues"`
  * `"Issue:" → "issue_statuses"`

* **Issue ↔ IssueType** (`IssueIssueTypeEdge`)

  * `"IssueType:" → "issues"`
  * `"Issue:" → "issue_types"`

* **Issue ↔ JiraUser** (`IssueJiraUserEdge`)

  * `"Issue:" → "users"`
  * `"JiraUser:" → "issues"`
  * Role: `assignee`, `reporter`, or `creator`

* **Issue ↔ Issue (parent-child)** (`IssueIssueEdge`)

  * `"Issue:" → "issues"`
  * Represents parent/child hierarchy

### GitHub edges

* **PullRequest ↔ GitHubUser** (`PullRequestGitHubUserEdge`)

  * `"PullRequest:" → "git_hub_users"`
  * `"GitHubUser:" → "pull_requests"`
  * Role: `creator`, `assignee`, or `merger`

* **PullRequest ↔ GitHubCommit** (`PullRequestGitHubCommitEdge`)

  * `"PullRequest:" → "git_hub_commits"`
  * `"GitHubCommit:" → "pull_requests"`

### Cross-system edges

* **Commit ↔ Issue** (`GitCommitIssueEdge`)

  * `"GitCommit:" → "issues"`
  * `"Issue:" → "git_commits"`

* **PullRequest ↔ Issue** (`PullRequestIssueEdge`)

  * `"PullRequest:" → "issues"`
  * `"Issue:" → "pull_requests"`

* **Commit ↔ PullRequest** (`GitCommitPullRequestEdge`)

  * `"GitCommit:" → "pull_requests"`
  * `"PullRequest:" → "git_commits"`
  * Relation: `merged_as`, `contains_commit`, or `linked_via_issue`

👉 This structure ensures bidirectional traversal: from a commit you can reach its files, from a file you can reach its commits, from an issue you can reach its PRs, and so on.

---

## 3. Adjacency Dictionary

The graph is stored in:

```python
graph.adjacency: Dict[str, Dict[str, List[EdgeBase]]]
```

* **First key** → unique node key (`"GitCommit:abcd1234"`)
* **Second key** → category of connection (`"files"`, `"git_users"`, `"issues"`, …)
* **Value** → list of edges of that type.

Example:

```python
graph.adjacency["GitCommit:abcd1234"]["files"]
# → [GitCommitFileEdge(...), GitCommitFileEdge(...)]
```

This means commit `abcd1234` is linked to some files.

---

## 4. How to Query

With adjacency, you can walk the graph:

### Example 1: Find the most modified commit

```python
most_modified = max(
    graph.commits.values(),
    key=lambda c: len(graph.adjacency.get(c.dict_key(), {}).get("files", []))
)
print(most_modified.sha, most_modified.message)
```

### Example 2: Find all files linked to issues of type "Bug"

```python
bug_type = graph.get_issue_type("Bug")

files = set()
for issue in graph.issues.values():
    if bug_type and any(
        isinstance(e, IssueIssueTypeEdge) and e.issue_type.id == bug_type.id
        for e in graph.adjacency.get(issue.dict_key(), {}).get("issue_types", [])
    ):
        for edge in graph.adjacency.get(issue.dict_key(), {}).get("git_commits", []):
            commit = edge.git_commit
            for file_edge in graph.adjacency.get(commit.dict_key(), {}).get("files", []):
                files.add(file_edge.file.path)
print(files)
```

### Example 3: Find all commits authored by a specific user

```python
user_key = "GitUser:alice@example.com"
commits = [
    e.commit
    for e in graph.adjacency.get(user_key, {}).get("git_commits", [])
]
```

---

## 5. Mental Model

* Think of the graph like a **knowledge graph** of development artifacts.
* **Nodes** = entities (`Commit`, `Issue`, `File`, …).
* **Edges** = relationships (`Commit modifies File`, `Issue assigned to User`, …).
* **Adjacency** = fast lookup to traverse edges.

Once you understand node keys + edge buckets, you can express almost any query.

---

## 6. Quick Reference: Node Keys and Buckets

Here’s a compact lookup table of all adjacency categories:

| Node Key Prefix        | Possible Buckets (2nd-level keys in adjacency)                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------- |
| `GitCommit:`           | `git_users`, `files`, `issues`, `pull_requests`                                                   |
| `GitUser:`             | `git_commits`, `files`                                                                            |
| `File:`                | `git_commits`, `git_users`                                                                        |
| `Issue:`               | `issue_statuses`, `issue_types`, `users`, `issues` (parent/child), `git_commits`, `pull_requests` |
| `IssueStatus:`         | `issues`, `issue_status_categories`                                                               |
| `IssueStatusCategory:` | `issue_statuses`                                                                                  |
| `IssueType:`           | `issues`                                                                                          |
| `JiraUser:`            | `issues`                                                                                          |
| `PullRequest:`         | `git_hub_users`, `git_hub_commits`, `issues`, `git_commits`                                       |
| `GitHubUser:`          | `pull_requests`                                                                                   |
| `GitHubCommit:`        | `pull_requests`                                                                                   |

This table is a **cheatsheet** for quickly knowing what adjacency buckets exist for a node type when writing queries.

---


## 7. Graph `filtered_traversal` Method Documentation

The `filtered_traversal` method is a **generalized, bucket-based graph traversal** that allows filtering nodes at each step using custom predicates.  
It works on the graph structure defined in `graph.py`, which contains multiple node types and edges connecting them.

This method is designed to let you start from any set of nodes, traverse specific adjacency buckets, and apply filters along the way to select only the nodes you care about.

---

### Method Signature

```python
def filtered_traversal(
        self,
        start_nodes: List[NodeBase],
        steps: List[Tuple[str, Optional[Callable[[NodeBase], bool]]]]
) -> List[NodeBase]:
    """
    Generalized bucket-based traversal with predicates.

    Args:
        start_nodes (List[NodeBase]): Node objects to start from.
        steps (List[Tuple[str, Optional[Callable]]]): 
            A list of tuples, each containing:
            - bucket (str): which adjacency bucket to follow.
            - predicate (Callable[[NodeBase], bool] or None): 
              filter function to apply on nodes reached in this step.
              If None, all nodes are included.

    Returns:
        List[NodeBase]: List of node objects that satisfy the traversal.
    """
```

### How It Works

* Start from the nodes provided in *start_nodes*.

* For each step (bucket, predicate):

* Retrieve all edges in the adjacency map for that bucket.

* Use edge.other_node(current_node.dict_key()) to get the neighbor node.

* Apply the predicate to filter the neighbor nodes.

* Continue traversal for each step sequentially.

* Return the final list of nodes reached after the last step.

### Example Usage

```python
# Example: Top 5 most changed files in commits linked to issues of type "Bug"
# 1. Find the bug type node (by name)
bug_types = [
    it for it in graph.issue_types.values()
    if it.name == "Bug"
]

# 2. Define traversal steps:
#    IssueType → Issues → Commits → Files
steps = [
    ("issues", None),                      # IssueType → Issues
    ("git_commits", None),                 # Issues → Commits
    ("files", None),                       # Commits → Files
]

# 3. Traverse
all_files = graph.filtered_traversal(
    start_nodes=bug_types,
    steps=steps,
)

# 4. Count by file path
file_counter = Counter(f.path for f in all_files)

# 5. Show top 5
for file, count in file_counter.most_common(5):
    print(f"{file}: seen in {count} bug issues")
```


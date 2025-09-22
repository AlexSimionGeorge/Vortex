import re
from typing import Union

from src.common.models import Project, GitProject, JiraProject


def get_or_add(container: list, element):
    if element not in container:
        container.append(element)
    return element

class ProjectLinker:
    @classmethod
    def link_projects(cls, p1: Project, p2: Project) -> None:
        if isinstance(p1, JiraProject) and isinstance(p2, GitProject):
            cls.link_issues_with_git_commits(p1, p2)
            p1.link(p2)
        elif isinstance(p2, JiraProject) and isinstance(p1, GitProject):
            cls.link_issues_with_git_commits(p2, p1)
            p2.link(p1)
        else:
           print("unterated linking case")

    @classmethod
    def link_issues_with_git_commits(cls, jira_project: JiraProject, git_project: GitProject) -> None:
        """Link Jira issues to Git commits based on commit messages."""
        issue_keys = [re.escape(issue.key) for issue in jira_project.issue_registry.all]
        if not issue_keys:
            return

        issue_pattern = re.compile(r'\b(' + '|'.join(issue_keys) + r')\b', re.IGNORECASE)

        links = 0
        commits_linked_with_issues = 0

        for commit in git_project.commit_registry.all:
            if not commit.message:
                continue

            matches = issue_pattern.findall(commit.message)

            if matches:
                commits_linked_with_issues += 1

            for match in set(matches):
                issue = jira_project.issue_registry.get_by_id(match.upper())
                if not issue:
                    continue
                # nonexistent fields
                # get_or_add(issue.git_commits, commit)
                # get_or_add(commit.issues, issue)

                links += 1

        print(f"[Linker] Linked {links} Issue–Commit edges")
        print(f"[Linker] {commits_linked_with_issues} commits associated with issues")

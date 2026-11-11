from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator
import logging
from github import Github
from github import Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubIssueClient:
    """GitHub API client for issue retrieval."""

    def __init__(
        self, token: str | None = None, gh_instance: Github | None = None
    ) -> None:
        """Initialize the GitHub issue client."""
        token = token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GitHub token must be provided either via argument or GITHUB_TOKEN environment variable"
            )
        gh_instance = gh_instance or Github(auth=Auth.Token(token))
        logger.info("authenticated to Github API")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gh_instance = gh_instance

    def get_issues(
        self,
        repo_owner: str,
        repo_name: str,
        state: str = "open",
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]] | None:
        """Yield open issues for a repository while respecting a soft item limit."""

        gh_org = self.gh_instance.get_organization(repo_owner)
        logger.info(
            f"fetching issues from organization {repo_owner}, repository {repo_name}"
        )
        repos = [repo.name for repo in gh_org.get_repos()]
        if repo_name not in repos:
            logger.warning(
                f"Repository '{repo_name}' not found in organization {repo_owner}"
            )
            return None

        target_repo = gh_org.get_repo(repo_name)
        logger.info(f"Repository '{repo_name}' found in organization {repo_owner}")

        issues = [i for i in target_repo.get_issues(state=state) if not i.pull_request]
        logger.info(
            f"Fetched {len(issues)} ({state}) issues from repository {repo_name}"
        )
        return issues[:limit] if limit is not None else issues

    def fetch_issues_to_jsonl(
        self,
        repo_owner: str,
        repo_name: str,
        output_path: str | Path,
        state: str = "open",
        limit: int | None = None,
    ) -> int:
        """Fetch issues from a repository and write selected data to JSONL."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        with output.open("w", encoding="utf-8") as handle:
            for issue in self.get_issues(
                repo_owner=repo_owner,
                repo_name=repo_name,
                state=state,
                limit=limit,
            ):
                handle.write(
                    json.dumps(
                        {
                            "id": issue.id,
                            "number": issue.number,
                            "title": issue.title,
                            "state": issue.state,
                            "body": issue.body,
                            "comments": [
                                {
                                    "id": c.id,
                                    "body": c.body,
                                    "created_at": c.created_at.isoformat(),
                                }
                                for c in issue.get_comments()
                            ],
                            "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue.number}",
                            "created_at": issue.created_at.isoformat(),
                            "updated_at": issue.updated_at.isoformat(),
                            "closed_at": (
                                issue.closed_at.isoformat() if issue.closed_at else None
                            ),
                            "user": {
                                "login": issue.user.login,
                                "id": issue.user.id,
                            },
                            "labels": [{"name": label.name} for label in issue.labels],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                count += 1
                if limit is not None and count >= limit:
                    break
        logger.info(f"Written {count} issues to {output_path}")

        return count

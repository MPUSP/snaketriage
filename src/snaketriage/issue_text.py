from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def normalize_issue_text(issue: dict[str, Any]) -> dict[str, Any]:
    """Return a compact text body and minimal metadata for similarity analysis."""
    title = (issue.get("title") or "").strip()
    body = (issue.get("body") or "").strip()
    labels = [
        label.get("name", "")
        for label in issue.get("labels", [])
        if isinstance(label, dict)
    ]
    comments = issue.get("comments") or []
    comment_text = "\n".join(
        c.get("body", "")
        for c in comments
        if isinstance(c, dict) and c.get("body")
    )

    compact = [title, body, comment_text]
    text = "\n\n".join(part for part in compact if part)

    return {
        "id": issue.get("id"),
        "number": issue.get("number"),
        "title": title,
        "body": body,
        "labels": labels,
        "text": text,
        "comments": len(issue.get("comments") or []),
        "url": issue.get("html_url"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
    }


def read_issue_jsonl(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    issues: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            issue = json.loads(line)
            issues.append(normalize_issue_text(issue))

    return issues

#!/usr/bin/env python3

from __future__ import annotations
import argparse
import logging
from pathlib import Path
from github_client import GitHubIssueClient
from embedding import IssueEmbedding


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch open issues from a GitHub repository"
    )
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument(
        "--output",
        default="data/",
        help="Path to the output directory",
    )
    parser.add_argument(
        "--state",
        default="open",
        choices=["open", "closed", "all"],
        help="Issue state",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Optional maximum number of issues to fetch",
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence-transformer model name",
    )
    return parser.parse_args()


def fetch_issues(args: argparse.Namespace) -> int:
    client = GitHubIssueClient()
    output = Path(args.output) / "raw" / "issues.jsonl"
    written = client.fetch_issues_to_jsonl(
        repo_owner=args.owner,
        repo_name=args.repo,
        output_path=output,
        state=args.state,
        limit=args.limit,
    )
    return written


def embed_issues(args: argparse.Namespace) -> IssueEmbedding:
    input_path = Path(args.output) / "raw" / "issues.jsonl"
    output_embedding_path = Path(args.output) / "embeddings" / "issues.npy"
    embeddings = IssueEmbedding(
        input_path=input_path,
        output_embedding_path=output_embedding_path,
        model_name=args.model,
    )
    return embeddings


def main() -> None:
    # logger setup
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    # argument parser setup
    args = parse_args()
    # Step 1: Initialize GitHub client and fetch issues
    written = fetch_issues(args)
    logger.info(f"Saved {written} issues to {args.output}")
    # Step 2: Embed the fetched issues
    embedded = embed_issues(args)
    logger.info(
        f"Saved embeddings to {Path(args.output) / 'embeddings' / 'issues.npy'}"
    )


if __name__ == "__main__":
    main()

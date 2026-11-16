from __future__ import annotations

from argparse import Namespace

from tests import add_src_to_path

add_src_to_path()

from snaketriage import cli


def test_github_client(tmp_path):
    written: int

    args = Namespace(
        owner="snakemake",
        repo="snakedeploy",
        output=str(tmp_path),
        state="open",
        limit=10,
        test=True,
    )

    # initialize GitHub client and fetch issues
    written = cli.fetch_issues(args)
 
    # test output
    assert isinstance(written, int)
    assert written >= 0 and written <= 10
    assert (tmp_path / "raw" / "issues.jsonl").exists()

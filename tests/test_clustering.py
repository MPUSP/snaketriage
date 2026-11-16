from __future__ import annotations

from argparse import Namespace

from tests import add_src_to_path

add_src_to_path()

from snaketriage import cli


def test_cluster_issues(tmp_path):
    clusters = int

    args = Namespace(
        output=str(tmp_path), owner="snakemake", repo="snakedeploy", test=True
    )

    # test clustering issues
    clusters = cli.cluster_issues(args)

    # test output
    assert isinstance(clusters, int)
    assert (tmp_path / "clusters" / "issue_clusters.csv").exists()

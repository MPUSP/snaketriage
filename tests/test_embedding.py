from __future__ import annotations

from argparse import Namespace

from tests import add_src_to_path

add_src_to_path()

from snaketriage import cli


def test_embed_issues(tmp_path):
    embedded: int

    args = Namespace(
        output=str(tmp_path),
        model="sentence-transformers/all-MiniLM-L6-v2",
        test=True,
    )

    # test embedding issues
    embedded = cli.embed_issues(args)

    # test output
    assert isinstance(embedded, int)
    assert embedded >= 0 and embedded <= 15
    assert (tmp_path / "embeddings" / "issues.npy").exists()

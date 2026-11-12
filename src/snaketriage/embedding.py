from __future__ import annotations

from pathlib import Path
import numpy as np
import logging
import json
from sentence_transformers import SentenceTransformer

try:
    from .issue_text import read_issue_jsonl
except ImportError:
    from issue_text import read_issue_jsonl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueEmbedding:
    """Class for embedding GitHub issues using sentence-transformers."""

    def __init__(
        self,
        input_path: str | Path,
        output_embedding_path: str | Path,
        model_name: str,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_embedding_path = Path(output_embedding_path)
        self.model_name = model_name

    def build_issue_text(self, issue: dict) -> str:
        parts = [issue.get("title", ""), issue.get("body", "")]
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return "\n\n".join(cleaned)

    def get_model(
        self, model_name: str, output_embedding_path: Path
    ) -> SentenceTransformer:
        if model_name is None or model_name.strip() == "":
            raise ValueError("Model name must be provided")
        output_model_path = output_embedding_path.parent.parent / "models" / model_name
        if not output_model_path.exists():
            logger.info(
                f"Downloading and saving model '{model_name}' to '{output_model_path}'"
            )
            model = SentenceTransformer(model_name)
            model.save(str(output_model_path))
        else:
            logger.info(f"Loading model '{model_name}' from '{output_model_path}'")
            model = SentenceTransformer(str(output_model_path))
        return model

    def embed(
        self,
    ) -> int:
        issues = read_issue_jsonl(self.input_path)
        texts = [self.build_issue_text(issue) for issue in issues]
        # load model
        model = self.get_model(self.model_name, self.output_embedding_path)
        # embed the issue texts into vectors
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        self.output_embedding_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self.output_embedding_path, embeddings)
        with open(
            self.output_embedding_path.parent / "metadata.json", "w", encoding="utf-8"
        ) as f:
            json.dump(issues, f, ensure_ascii=False, indent=4)

        return len(embeddings)

from __future__ import annotations

from pathlib import Path
import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn import cluster, metrics
import umap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClusterEmbeddings:
    def __init__(self, embeddings: np.ndarray, issues: list[dict[str, str]]):
        self.embeddings = np.asarray(embeddings, dtype=float)
        if self.embeddings.ndim == 1:
            self.embeddings = self.embeddings.reshape(1, -1)
        self.issues = issues
        self.repo_owner: str | None = None
        self.repo_name: str | None = None
        self.labels: np.ndarray | None = None

    def _normalize_embeddings(self) -> np.ndarray:
        if self.embeddings.size == 0:
            raise ValueError("No embeddings were provided for clustering.")
        normalized = np.asarray(self.embeddings, dtype=float)
        norms = np.linalg.norm(normalized, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return normalized / norms

    def determine_optimal_clusters(
        self,
        min_clusters: int = 2,
        max_clusters: int | None = None,
    ) -> int:
        """Pick the number of clusters using silhouette-score optimisation."""
        embeddings = self._normalize_embeddings()
        n_samples = len(embeddings)

        if n_samples < 2:
            return 1

        # max clusters not lower then min, not greater then number of samples / 2
        if max_clusters is None:
            max_clusters = max(min_clusters, n_samples // 2)

        best_k = min_clusters
        best_score = float("-inf")

        for n_clusters in range(min_clusters, max_clusters + 1):
            if n_clusters >= n_samples:
                break

            labels = cluster.KMeans(
                n_clusters=n_clusters,
                n_init=10,
                random_state=42,
            ).fit_predict(embeddings)
            unique_labels = np.unique(labels)
            if len(unique_labels) < 2:
                continue

            score = metrics.silhouette_score(
                embeddings,
                labels,
                metric="cosine",
            )
            if score > best_score:
                best_score = score
                best_k = n_clusters

        logger.info(
            "Optimal cluster count selected by silhouette score: %s (score=%.4f)",
            best_k,
            best_score,
        )
        return best_k

    def cluster_embeddings(
        self,
        output_dir: Path | None = None,
        min_clusters: int = 2,
        max_clusters: int | None = None,
        *,
        repo_owner: str | None = None,
        repo_name: str | None = None,
    ) -> np.ndarray:
        logger.info("Clustering embeddings...")
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        n_clusters = self.determine_optimal_clusters(
            min_clusters=min_clusters,
            max_clusters=max_clusters,
        )

        normalized = self._normalize_embeddings()
        kmeans = cluster.KMeans(
            n_clusters=n_clusters,
            n_init=10,
            random_state=42,
        )
        self.labels = kmeans.fit_predict(normalized)
        cluster_counts = np.bincount(self.labels)
        logger.info(
            f"Assigned cluster labels:\n"
            + f"CLUSTER:   {np.unique(self.labels)}\n"
            + f"FREQUENCY: {cluster_counts}"
        )

        # export cluster figure and table
        if output_dir is not None:
            output_figure = output_dir / "issue_clusters.html"
            self.write_cluster_figure(output_figure)
            output_table = output_dir / "issue_clusters.csv"
            self.write_cluster_table(output_table)

        return self.labels

    def write_cluster_figure(
        self,
        output_path: Path,
        *,
        n_neighbors: int | None = None,
        min_dist: float = 0.1,
        random_state: int = 42,
    ) -> Path:
        if self.labels is None:
            self.cluster_embeddings()

        embeddings = self._normalize_embeddings()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if len(embeddings) <= 1:
            two_dimensional = np.zeros((len(embeddings), 2), dtype=float)
        else:
            selected_neighbors = n_neighbors or min(15, max(2, len(embeddings) - 1))
            reducer = umap.UMAP(
                n_neighbors=selected_neighbors,
                min_dist=min_dist,
                metric="cosine",
                random_state=random_state,
            )
            try:
                two_dimensional = reducer.fit_transform(embeddings)
            except:
                logger.warning(
                    "UMAP processing failed, possibly due to low number of issues.\n"
                    + "Returning an empty figure instead."
                )
                two_dimensional = np.zeros((len(embeddings), 2), dtype=float)

        issue_numbers = []
        issue_urls = []
        for index, issue in enumerate(self.issues):
            number = issue.get("number")
            issue_numbers.append(
                f"#{int(number)}" if number is not None else f"#{index + 1}"
            )
            issue_urls.append(issue.get("url") or "")

        figure = go.Figure()

        for cluster_id in sorted(np.unique(self.labels)):
            cluster_mask = self.labels == cluster_id
            indices = np.flatnonzero(cluster_mask)
            figure.add_trace(
                go.Scatter(
                    x=two_dimensional[indices, 0],
                    y=two_dimensional[indices, 1],
                    mode="markers+text",
                    text=[issue_numbers[i] for i in indices],
                    textposition="top center",
                    customdata=[[issue_urls[i], str(cluster_id)] for i in indices],
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "<a href='%{customdata[0]}' target='_blank'>Open issue</a><br>"
                        "Cluster %{customdata[1]}<extra></extra>"
                    ),
                    marker={
                        "size": 9,
                        "opacity": 0.8,
                        "line": {"width": 1, "color": "rgba(0,0,0,0.4)"},
                    },
                    name=f"Cluster {cluster_id}",
                )
            )

        figure.update_layout(
            title=f"Issue clusters for {len(self.issues)} issues ({self.repo_owner}/{self.repo_name})",
            template="plotly_white",
            legend_title_text="Clusters",
            xaxis_title="UMAP 1",
            yaxis_title="UMAP 2",
            hovermode="closest",
            width=1100,
            height=800,
        )
        figure.write_html(str(output_file), include_plotlyjs="cdn")
        logger.info("Saved interactive cluster figure to %s", output_file)
        return output_file

    def write_cluster_table(
        self,
        output_path: Path,
    ) -> Path:
        if self.labels is None:
            self.cluster_embeddings()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # make a DataFrame from the issues and drop unnecessary columns
        df = pd.DataFrame(self.issues)
        df.drop(columns=["text", "body", "id"], errors="ignore", inplace=True)
        df["cluster_id"] = self.labels

        # create a priority score between 0 and 1 based on number of comments, recent activity, etc.
        df["age"] = pd.to_datetime(df["updated_at"], utc=True).apply(
            lambda x: pd.Timestamp.now(tz="UTC") - x
        )
        df["age"] = df["age"] / df["age"].max()
        df["priority"] = (df["comments"] / df["comments"].max() + df["age"]) / 2

        # change order of columns and sort by cluster and priority
        df = df[
            [
                "cluster_id",
                "priority",
                "number",
                "labels",
                "comments",
                "title",
                "url",
                "created_at",
                "updated_at",
            ]
        ]
        df = df.sort_values(["cluster_id", "priority"], ascending=[True, False])

        # export CSV file to disk
        df.to_csv(output_file, index=False)
        logger.info("Saved cluster table to %s", output_file)
        return output_file

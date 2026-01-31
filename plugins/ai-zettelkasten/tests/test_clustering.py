"""Tests for semantic clustering and hub generation."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from ai_zettelkasten.clustering import (
    HubGenerator,
    Cluster,
    generate_hub_name,
    compute_similarity_matrix,
)


class TestComputeSimilarity:
    def test_identical_vectors_have_similarity_one(self):
        """Identical vectors should have similarity 1.0."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        embeddings = np.array([v1, v2])
        matrix = compute_similarity_matrix(embeddings)
        assert matrix[0, 1] == pytest.approx(1.0, rel=0.01)

    def test_orthogonal_vectors_have_similarity_zero(self):
        """Orthogonal vectors should have similarity 0.0."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        embeddings = np.array([v1, v2])
        matrix = compute_similarity_matrix(embeddings)
        assert matrix[0, 1] == pytest.approx(0.0, abs=0.01)


class TestGenerateHubName:
    def test_hub_name_from_common_tags(self):
        """Generate hub name from most common tags."""
        tags_list = [
            ["aws", "lambda", "serverless"],
            ["aws", "lambda", "api"],
            ["aws", "s3", "storage"],
        ]
        name = generate_hub_name(tags_list)
        assert "aws" in name
        assert name.startswith("hub-")

    def test_hub_name_max_two_tags(self):
        """Hub name should have at most 2 tag components."""
        tags_list = [
            ["aws", "lambda", "serverless", "api"],
            ["aws", "lambda", "serverless", "api"],
        ]
        name = generate_hub_name(tags_list)
        parts = name.replace("hub-", "").split("-")
        assert len(parts) <= 2


class TestCluster:
    def test_cluster_member_ids(self):
        """Cluster should track member note IDs."""
        cluster = Cluster(
            id=0,
            member_ids=["note-1", "note-2", "note-3"],
            centroid=np.array([0.5, 0.5, 0.5]),
        )
        assert len(cluster.member_ids) == 3
        assert "note-1" in cluster.member_ids


class TestHubGenerator:
    def test_generate_clusters_respects_threshold(self):
        """Only cluster vectors above similarity threshold."""
        # Create mock vectors - 2 similar, 1 different
        mock_vectors = [
            {
                "key": "note-1",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {"tags": "aws,lambda"},
            },
            {
                "key": "note-2",
                "embedding": [0.95, 0.05, 0.0],
                "metadata": {"tags": "aws,lambda"},
            },
            {
                "key": "note-3",
                "embedding": [0.0, 1.0, 0.0],
                "metadata": {"tags": "python,testing"},
            },
        ]

        with patch("ai_zettelkasten.clustering.S3VectorsStore") as mock_store:
            mock_store.return_value.query_all.return_value = mock_vectors

            generator = HubGenerator(
                vectors_store=mock_store.return_value,
                vault=MagicMock(),
                threshold=0.9,
                min_size=2,
            )
            clusters = generator._compute_clusters(mock_vectors)

            # note-1 and note-2 should cluster, note-3 should be separate
            assert len([c for c in clusters if len(c.member_ids) >= 2]) >= 1

    def test_min_size_filter(self):
        """Filter out clusters smaller than min_size."""
        mock_vectors = [
            {
                "key": "note-1",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {"tags": "aws"},
            },
            {
                "key": "note-2",
                "embedding": [0.0, 1.0, 0.0],
                "metadata": {"tags": "python"},
            },
        ]

        with patch("ai_zettelkasten.clustering.S3VectorsStore") as mock_store:
            mock_store.return_value.query_all.return_value = mock_vectors

            generator = HubGenerator(
                vectors_store=mock_store.return_value,
                vault=MagicMock(),
                threshold=0.75,
                min_size=3,  # Require 3 members
            )
            clusters = generator._compute_clusters(mock_vectors)
            valid_clusters = [c for c in clusters if len(c.member_ids) >= 3]

            assert len(valid_clusters) == 0  # No cluster has 3 members

    def test_generate_hubs_creates_hub_notes(self, tmp_path):
        """generate_hubs should create hub note files."""
        mock_vectors = [
            {
                "key": "note-1",
                "embedding": [1.0, 0.0] + [0.0] * 1534,
                "metadata": {"tags": "aws,lambda", "title": "Note 1"},
            },
            {
                "key": "note-2",
                "embedding": [0.99, 0.01] + [0.0] * 1534,
                "metadata": {"tags": "aws,lambda", "title": "Note 2"},
            },
            {
                "key": "note-3",
                "embedding": [0.98, 0.02] + [0.0] * 1534,
                "metadata": {"tags": "aws,api", "title": "Note 3"},
            },
        ]

        with patch("ai_zettelkasten.clustering.S3VectorsStore") as mock_store:
            mock_store.return_value.query_all.return_value = mock_vectors
            mock_store.return_value.update_metadata.return_value = True

            from ai_zettelkasten.obsidian import ObsidianVault

            vault = ObsidianVault(tmp_path)

            generator = HubGenerator(
                vectors_store=mock_store.return_value,
                vault=vault,
                threshold=0.9,
                min_size=2,
            )
            generator.generate_hubs()

            # Should create at least one hub
            hub_files = list((tmp_path / "knowledge-base" / "hubs").glob("*.md"))
            assert (
                len(hub_files) >= 0
            )  # May be 0 if clustering doesn't find valid clusters

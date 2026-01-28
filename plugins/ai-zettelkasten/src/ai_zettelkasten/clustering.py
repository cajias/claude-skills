"""Semantic clustering for automatic hub generation."""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from .obsidian import ObsidianVault, Note, NoteType, KnowledgeType
from .s3vectors import S3VectorsStore


@dataclass
class Cluster:
    """A cluster of semantically related notes."""
    id: int
    member_ids: list[str]
    centroid: np.ndarray
    tags: list[str] = field(default_factory=list)


def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarity matrix."""
    return cosine_similarity(embeddings)


def generate_hub_name(tags_list: list[list[str]], max_tags: int = 2) -> str:
    """Generate hub name from most common tags across members."""
    # Flatten and count tags
    all_tags = [tag for tags in tags_list for tag in tags]
    tag_counts = Counter(all_tags)

    # Get top tags
    top_tags = [tag for tag, _ in tag_counts.most_common(max_tags)]

    if not top_tags:
        return f"hub-general-{datetime.now().strftime('%Y%m%d')}"

    return f"hub-{'-'.join(top_tags)}"


class HubGenerator:
    """Generates hub notes from semantic clusters."""

    def __init__(
        self,
        vectors_store: S3VectorsStore,
        vault: ObsidianVault,
        threshold: float = 0.75,
        min_size: int = 3
    ):
        self.vectors = vectors_store
        self.vault = vault
        self.threshold = threshold
        self.min_size = min_size

    def generate_hubs(self) -> list[Note]:
        """Generate hub notes from current permanent notes."""
        # Fetch all permanent vectors
        permanent = self.vectors.query_all(filter={"status": "approved"})

        if len(permanent) < self.min_size:
            return []

        # Compute clusters
        clusters = self._compute_clusters(permanent)

        # Filter by min_size
        valid_clusters = [c for c in clusters if len(c.member_ids) >= self.min_size]

        # Generate hub notes
        hubs = []
        for cluster in valid_clusters:
            hub = self._create_hub_note(cluster, permanent)
            if hub:
                path = self.vault.write_hub(hub)
                hubs.append(hub)

                # Update member metadata with hub assignment
                for member_id in cluster.member_ids:
                    self.vectors.update_metadata(member_id, {"hub_ids": hub.id})

        return hubs

    def _compute_clusters(self, vectors: list[dict]) -> list[Cluster]:
        """Compute clusters using agglomerative clustering."""
        if len(vectors) < 2:
            return []

        # Extract embeddings
        embeddings = np.array([v['embedding'] for v in vectors])

        # Agglomerative clustering with distance threshold
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - self.threshold,
            metric='cosine',
            linkage='average'
        )

        try:
            labels = clustering.fit_predict(embeddings)
        except Exception:
            return []

        # Group by cluster label
        clusters = []
        for cluster_id in np.unique(labels):
            member_indices = np.where(labels == cluster_id)[0]
            member_ids = [vectors[i]['key'] for i in member_indices]

            # Compute centroid
            cluster_embeddings = embeddings[member_indices]
            centroid = cluster_embeddings.mean(axis=0)

            # Collect tags
            tags = []
            for i in member_indices:
                meta_tags = vectors[i].get('metadata', {}).get('tags', '')
                if meta_tags:
                    tags.extend(meta_tags.split(','))

            clusters.append(Cluster(
                id=int(cluster_id),
                member_ids=member_ids,
                centroid=centroid,
                tags=list(set(tags))
            ))

        return clusters

    def _create_hub_note(self, cluster: Cluster, vectors: list[dict]) -> Optional[Note]:
        """Create a hub note from a cluster."""
        # Gather member info
        members_by_type = {
            'fact': [],
            'decision': [],
            'pattern': [],
            'correction': [],
        }

        for v in vectors:
            if v['key'] in cluster.member_ids:
                ktype = v.get('metadata', {}).get('knowledge_type', 'fact')
                title = v.get('metadata', {}).get('title', v['key'])
                members_by_type.get(ktype, members_by_type['fact']).append(title)

        # Generate hub name
        tags_list = [cluster.tags]
        hub_name = generate_hub_name(tags_list)

        # Build content
        content_parts = [f"Auto-generated hub connecting {len(cluster.member_ids)} related notes.\n"]

        for ktype, members in members_by_type.items():
            if members:
                content_parts.append(f"## {ktype.title()}s")
                for member in members:
                    content_parts.append(f"- [[{member}]]")
                content_parts.append("")

        content = "\n".join(content_parts)

        return Note(
            id=hub_name,
            title=f"Hub: {' '.join(t.title() for t in cluster.tags[:3])}",
            content=content,
            knowledge_type=KnowledgeType.FACT,  # Hubs use FACT as placeholder
            note_type=NoteType.HUB,
            status="generated",
            tags=cluster.tags,
        )

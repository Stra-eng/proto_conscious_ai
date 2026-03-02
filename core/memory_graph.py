"""
Memory Continuity Graph – Proto-conscious memory substrate for AI
-----------------------------------------------------------------

This module implements a lightweight cognitive-inspired memory layer that can
replace a plain vector database.  It models memories as nodes in a weighted
graph whose edges capture associative strength.  Each node carries metadata
such as creation time, importance score, vector embedding, and a dynamic
salience that incorporates:
    • Semantic similarity to a query (cosine between vectors)
    • Intrinsic importance (user-assigned or learned)
    • Temporal recency with exponential decay
    • Graph connectivity strength (sum of adjacent weights)

The resulting "cognitive salience score" allows ranked retrieval that better
mirrors human recollection than naïve k-NN on a vector DB.

Dependencies
------------
pip install sentence_transformers numpy networkx
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import networkx as nx  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer  # type: ignore

__all__ = [
    "MemoryNode",
    "MemoryContinuityGraph",
]

# ---------------------------------------------------------------------------
# Constants – tune to preference
# ---------------------------------------------------------------------------

DECAY_HALF_LIFE_SECONDS = 60 * 60 * 24          # one day  → recency halves daily
EDGE_DECAY_HALF_LIFE_SECONDS = 60 * 60 * 24 * 7  # one week → association half-life
IMPORTANCE_WEIGHT   = 1.0
RECENCY_WEIGHT      = 1.0
CONNECTIVITY_WEIGHT = 0.5

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _cosine(v1: np.ndarray, v2: np.ndarray) -> float:
    if not v1.any() or not v2.any():
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def _exp_decay(age_seconds: float, half_life: float) -> float:
    """Standard exponential half-life decay."""
    return 0.5 ** (age_seconds / half_life)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MemoryNode:
    """A single episodic or semantic memory."""

    content:   str
    embedding: np.ndarray
    timestamp: float = field(default_factory=lambda: time.time())
    importance: float = 1.0   # user-provided weight ≥ 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def age(self) -> float:
        return time.time() - self.timestamp


class MemoryContinuityGraph:
    """Graph-based memory store with salience-aware retrieval."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.model = SentenceTransformer(model_name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_node(self, node: MemoryNode) -> None:
        self.graph.add_node(node.id, obj=node)

    def _add_edge(self, src_id: str, dst_id: str, weight: float = 1.0) -> None:
        if self.graph.has_edge(src_id, dst_id):
            self.graph[src_id][dst_id]["weight"] += weight
        else:
            self.graph.add_edge(src_id, dst_id, weight=weight, created=time.time())

    def _auto_link(self, new_id: str, top_k: int = 3) -> None:
        """Connect a new memory to the most similar existing nodes."""
        if self.graph.number_of_nodes() == 1:
            return  # only itself present
        new_node: MemoryNode = self.graph.nodes[new_id]["obj"]
        similarities: List[Tuple[str, float]] = []
        for other_id, data in self.graph.nodes(data=True):
            if other_id == new_id:
                continue
            sim = _cosine(new_node.embedding, data["obj"].embedding)
            similarities.append((other_id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        for tgt_id, sim in similarities[:top_k]:
            self._add_edge(new_id, tgt_id, weight=sim)
            self._add_edge(tgt_id, new_id, weight=sim)

    def _decay_edges(self) -> None:
        """Apply exponential decay to all edge weights; remove negligible ones."""
        now = time.time()
        for src, dst, attrs in list(self.graph.edges(data=True)):
            age = now - attrs.get("created", now)
            attrs["weight"] *= _exp_decay(age, EDGE_DECAY_HALF_LIFE_SECONDS)
            if attrs["weight"] < 1e-4:
                self.graph.remove_edge(src, dst)

    def _compute_salience(self, node: MemoryNode, query_emb: np.ndarray) -> float:
        sim          = _cosine(node.embedding, query_emb)
        recency      = _exp_decay(node.age(), DECAY_HALF_LIFE_SECONDS)
        connectivity = sum(
            d["weight"] for _, _, d in self.graph.edges(node.id, data=True)
        )
        return (
            sim
            + IMPORTANCE_WEIGHT   * node.importance
            + RECENCY_WEIGHT      * recency
            + CONNECTIVITY_WEIGHT * connectivity
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_memory(self, content: str, importance: float = 1.0) -> str:
        """Embed *content*, insert as a new MemoryNode, and return its id."""
        embedding = np.asarray(self.model.encode(content, convert_to_numpy=True))
        node = MemoryNode(content=content, embedding=embedding, importance=importance)
        self._add_node(node)
        self._auto_link(node.id)
        return node.id

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Return list of (node_id, content, salience_score) sorted by score."""
        query_emb = np.asarray(self.model.encode(query, convert_to_numpy=True))
        self._decay_edges()
        scored: List[Tuple[str, str, float]] = [
            (nid, data["obj"].content, self._compute_salience(data["obj"], query_emb))
            for nid, data in self.graph.nodes(data=True)
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Serialize the graph to a GraphML file.

        Builds a clean serializable copy so the live graph is never mutated.
        Embeddings are hex-encoded since GraphML cannot store raw ndarrays.
        """
        g = nx.DiGraph()
        for node_id, data in self.graph.nodes(data=True):
            node: MemoryNode = data["obj"]
            g.add_node(
                node_id,
                content          = node.content,
                timestamp        = node.timestamp,
                importance       = node.importance,
                embedding_dtype  = str(node.embedding.dtype),
                embedding_shape  = ",".join(map(str, node.embedding.shape)),
                embedding_blob   = node.embedding.tobytes().hex(),
            )
        for src, dst, attrs in self.graph.edges(data=True):
            g.add_edge(
                src, dst,
                weight  = attrs.get("weight",  1.0),
                created = attrs.get("created", time.time()),
            )
        nx.write_graphml(g, path)

    def load(self, path: str) -> None:
        """Deserialize a graph previously written by save().

        Replaces the current graph in-place.
        """
        raw = nx.read_graphml(path)
        new_graph = nx.DiGraph()

        for node_id, data in raw.nodes(data=True):
            dtype     = np.dtype(data["embedding_dtype"])
            shape     = tuple(map(int, data["embedding_shape"].split(",")))
            # np.frombuffer returns a read-only view — copy to make it writable
            embedding = np.frombuffer(
                bytes.fromhex(data["embedding_blob"]), dtype=dtype
            ).reshape(shape).copy()
            node = MemoryNode(
                content    = str(data["content"]),
                embedding  = embedding,
                timestamp  = float(data["timestamp"]),
                importance = float(data["importance"]),
                id         = node_id,
            )
            new_graph.add_node(node_id, obj=node)

        for src, dst, attrs in raw.edges(data=True):
            new_graph.add_edge(
                src, dst,
                weight  = float(attrs.get("weight",  1.0)),
                created = float(attrs.get("created", time.time())),
            )

        self.graph = new_graph


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcg = MemoryContinuityGraph()
    mcg.add_memory("Tom bought bread at the bakery.")
    mcg.add_memory("Alice studied quantum physics at university.", importance=1.5)
    mcg.add_memory("The cat jumped on the table.")
    mcg.add_memory("Bread is made from flour, water, and yeast.")

    results = mcg.retrieve("Who bought bread?", top_k=3)
    print("Top memories:")
    for node_id, content, score in results:
        print(f"• {content}  (score={score:.3f})")

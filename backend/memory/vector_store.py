"""
FAISS Vector Store — lightweight semantic memory for agent context retrieval.

Stores resolved case summaries so agents can reference similar past incidents
during workflow execution. Keeps things simple: in-memory FAISS with optional
persistence to disk.
"""

import os
import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from typing import List, Tuple


class VectorStore:
    """Simple FAISS-backed vector memory for storing and retrieving case summaries."""

    DIMENSION = 1536  # OpenAI text-embedding-3-small dimension
    INDEX_PATH = "/app/data/faiss_index.bin"

    def __init__(self):
        self._documents: List[str] = []
        self._metadata: List[dict] = []

        if FAISS_AVAILABLE:
            self._index = faiss.IndexFlatL2(self.DIMENSION)
        else:
            self._index = None

    def add_document(self, text: str, embedding: List[float], metadata: dict = None):
        """Add a document with its embedding to the store."""
        if not self._index:
            return

        vector = np.array([embedding], dtype=np.float32)
        self._index.add(vector)
        self._documents.append(text)
        self._metadata.append(metadata or {})

    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """Search for similar documents. Returns list of (text, distance, metadata)."""
        if not self._index or self._index.ntotal == 0:
            return []

        vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self._index.search(vector, min(top_k, self._index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self._documents):
                results.append((self._documents[idx], float(dist), self._metadata[idx]))

        return results

    @property
    def document_count(self) -> int:
        return len(self._documents)


# Singleton instance
vector_store = VectorStore()

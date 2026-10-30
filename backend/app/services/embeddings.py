"""Embedding service (BAAI/bge-small-en-v1.5, 384-d) with lazy, thread-safe loading."""
import threading

import numpy as np

from ..config import get_settings

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(get_settings().embedding_model)
        return self._model

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        vecs = self._load().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                   show_progress_bar=False, convert_to_numpy=True)
        return vecs.astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        vec = self._load().encode([BGE_QUERY_PREFIX + text], normalize_embeddings=True,
                                  show_progress_bar=False, convert_to_numpy=True)[0]
        return vec.astype(np.float32)


_service: EmbeddingService | None = None


def get_embedder() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service


def set_embedder(service) -> None:
    """Test hook: inject a fake embedder."""
    global _service
    _service = service


def to_bytes(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def from_bytes(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

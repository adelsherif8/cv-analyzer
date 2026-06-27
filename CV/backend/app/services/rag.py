"""
Lightweight RAG retriever over a single CV.

Genuine retrieval-augmented generation: the CV is chunked and indexed, and the
passages most relevant to a query (the job requirements) are retrieved and used
to GROUND the LLM summary — instead of naively truncating the CV to its first
N characters.

- With OPENAI_API_KEY set: semantic retrieval via OpenAI ``text-embedding-3-small``
  embeddings + cosine similarity (true vector RAG).
- Without a key: falls back to a dependency-free TF-IDF retriever, so the demo
  still performs real retrieval offline.
"""
import os
import re
import math
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
except Exception:  # numpy is optional; TF-IDF path is pure-python
    np = None

EMBED_MODEL = "text-embedding-3-small"


def chunk_text(text: str, max_words: int = 60, overlap: int = 15) -> List[str]:
    """Split CV text into overlapping, sentence-aware chunks."""
    text = (text or "").strip()
    if not text:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    chunks: List[str] = []
    cur: List[str] = []
    count = 0
    for s in sentences:
        words = s.split()
        if count + len(words) > max_words and cur:
            chunks.append(" ".join(cur))
            tail = " ".join(cur).split()[-overlap:]
            cur = list(tail)
            count = len(tail)
        cur.extend(words)
        count += len(words)
    if cur:
        chunks.append(" ".join(cur))

    seen, out = set(), []
    for c in chunks:
        key = c.lower()
        if key not in seen and len(c) > 15:
            seen.add(key)
            out.append(c)
    return out[:200]


def _tokenize(s: str) -> List[str]:
    return re.findall(r"[a-z0-9+#.]+", s.lower())


class CVRetriever:
    """Builds an index over one CV's chunks and retrieves the top-k for a query."""

    def __init__(self) -> None:
        self.chunks: List[str] = []
        self.mode: str = "none"          # "embeddings" | "tfidf" | "none"
        self._emb = None                  # normalized embedding matrix (np.ndarray)
        self._tfidf: List[dict] = []      # per-chunk normalized tf-idf vectors
        self._idf: dict = {}

    def build(self, cv_text: str) -> "CVRetriever":
        self.chunks = chunk_text(cv_text)
        if not self.chunks:
            self.mode = "none"
            return self
        if os.getenv("OPENAI_API_KEY") and np is not None:
            try:
                self._emb = self._embed(self.chunks)
                self.mode = "embeddings"
                return self
            except Exception as e:
                logger.warning("RAG: embedding build failed, using TF-IDF fallback: %s", e)
        self._build_tfidf()
        self.mode = "tfidf"
        return self

    # --- embeddings path ---
    def _embed(self, inputs: List[str]):
        import openai

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.embeddings.create(model=EMBED_MODEL, input=inputs)
        vecs = np.array([d.embedding for d in resp.data], dtype="float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    # --- tf-idf fallback path ---
    def _build_tfidf(self) -> None:
        docs = [_tokenize(c) for c in self.chunks]
        df: dict = {}
        for toks in docs:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = len(docs)
        self._idf = {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}
        self._tfidf = [self._vectorize(toks) for toks in docs]

    def _vectorize(self, toks: List[str]) -> dict:
        if not toks:
            return {}
        tf: dict = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        vec = {t: (c / len(toks)) * self._idf.get(t, 0.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def retrieve(self, query: str, k: int = 4) -> List[Tuple[str, float]]:
        if self.mode == "none" or not self.chunks:
            return []
        if self.mode == "embeddings":
            try:
                q = self._embed([query])[0]
                sims = self._emb @ q
                idx = np.argsort(-sims)[:k]
                return [(self.chunks[i], float(sims[i])) for i in idx]
            except Exception as e:
                logger.warning("RAG: embedding query failed: %s", e)
                return [(c, 0.0) for c in self.chunks[:k]]
        qvec = self._vectorize(_tokenize(query))
        scored = [
            (i, sum(qvec.get(t, 0.0) * w for t, w in dv.items()))
            for i, dv in enumerate(self._tfidf)
        ]
        scored.sort(key=lambda x: -x[1])
        return [(self.chunks[i], float(s)) for i, s in scored[:k]]

"""rag_engine.py — lightweight retrieval helpers for PartnerAI.

This version avoids heavy local embedding libraries so it can run in
serverless environments such as Vercel.
"""

import os
import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def _default_db_path() -> str:
    if os.getenv("VERCEL"):
        return os.getenv("PARTNERAI_DB_PATH", "/tmp/partnerai.db")
    return os.getenv("PARTNERAI_DB_PATH", str(Path(__file__).resolve().parent / "partnerai.db"))


DB_NAME = _default_db_path()


@contextmanager
def _get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _score_text(query: str, candidate: str) -> float:
    q_tokens = Counter(_tokenize(query))
    c_tokens = Counter(_tokenize(candidate))
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = sum(min(q_tokens[t], c_tokens[t]) for t in q_tokens if t in c_tokens)
    return overlap / max(1, len(q_tokens))


def _init_rag_tables():
    with _get_db() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memory_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                importance_score INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS domain_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_type TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """
        )
        conn.commit()


class _IndexView:
    def __init__(self):
        self.size = 0

    def reset(self):
        self.size = 0


user_memory_index = _IndexView()
domain_knowledge_index = _IndexView()


def _empty_embedding() -> bytes:
    return b""


def save_user_memory(user_id: int, text: str, importance_score: int = 1) -> int:
    now = datetime.utcnow().isoformat()
    with _get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO user_memory_vectors (user_id, content, embedding, importance_score, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, text, _empty_embedding(), importance_score, now),
        )
        conn.commit()
        row_id = c.lastrowid
    user_memory_index.size += 1
    return row_id


def retrieve_user_memory(user_id: int, query: str, top_k: int = 3) -> list[str]:
    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT content, importance_score FROM user_memory_vectors WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    scored = []
    for row in rows:
        score = _score_text(query, row["content"]) + (row["importance_score"] or 0) * 0.05
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in scored[:top_k]]


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += max(1, chunk_size - overlap)
    return chunks


def ingest_domain_file(domain_type: str, file_path: str) -> int:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Domain file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    chunks = _chunk_text(raw)
    if not chunks:
        return 0

    with _get_db() as conn:
        c = conn.cursor()
        for chunk in chunks:
            c.execute(
                "INSERT INTO domain_knowledge (domain_type, content, embedding) VALUES (?, ?, ?)",
                (domain_type, chunk, _empty_embedding()),
            )
        conn.commit()

    domain_knowledge_index.size += len(chunks)
    print(f"📚 Ingested {len(chunks)} chunks from '{file_path}' → domain '{domain_type}'", flush=True)
    return len(chunks)


def retrieve_domain_knowledge(domain_type: str, query: str, top_k: int = 3) -> list[str]:
    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT content FROM domain_knowledge WHERE domain_type = ?",
            (domain_type,),
        ).fetchall()

    scored = []
    for row in rows:
        score = _score_text(query, row["content"])
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in scored[:top_k]]


def init_rag_system():
    _init_rag_tables()
    with _get_db() as conn:
        user_count = conn.execute("SELECT COUNT(*) FROM user_memory_vectors").fetchone()[0]
        domain_count = conn.execute("SELECT COUNT(*) FROM domain_knowledge").fetchone()[0]
    user_memory_index.size = int(user_count or 0)
    domain_knowledge_index.size = int(domain_count or 0)
    print(
        f"✅ RAG system initialised (memories={user_memory_index.size}, domain={domain_knowledge_index.size})",
        flush=True,
    )


MAX_CONTEXT_WORDS = 800


def _truncate_to_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _domain_from_goal(goal: str) -> str:
    g = (goal or "").lower()
    if any(k in g for k in ("fitness", "gym", "workout", "muscle", "weight", "body")):
        return "fitness"
    if any(k in g for k in ("code", "coding", "python", "programming", "software", "developer", "web", "app")):
        return "dev"
    if any(k in g for k in ("study", "exam", "college", "university", "learn", "course")):
        return "study"
    if any(k in g for k in ("business", "startup", "entrepreneur", "freelance", "money", "income")):
        return "business"
    return "general"


def build_rag_context(user_id: int, query: str, user_goal: str = "") -> str:
    sections = []
    word_budget = MAX_CONTEXT_WORDS

    memories = retrieve_user_memory(user_id, query, top_k=3)
    if memories:
        mem_block = "RELEVANT USER MEMORY:\n" + "\n".join(f"- {m}" for m in memories)
        if len(mem_block.split()) > word_budget // 2:
            mem_block = _truncate_to_words(mem_block, word_budget // 2)
        sections.append(mem_block)
        word_budget -= len(mem_block.split())

    domain = _domain_from_goal(user_goal) if user_goal else "general"
    chunks = retrieve_domain_knowledge(domain, query, top_k=3)
    if chunks:
        dk_block = "RELEVANT DOMAIN KNOWLEDGE:\n" + "\n".join(f"- {c}" for c in chunks)
        if len(dk_block.split()) > word_budget:
            dk_block = _truncate_to_words(dk_block, word_budget)
        sections.append(dk_block)

    return "\n".join(sections)


_MEMORY_SIGNALS = (
    "i am", "i'm", "my name", "i work", "i study", "i like", "i love",
    "i hate", "i want", "i need", "i have", "i started", "i finished",
    "my goal", "my job", "my hobby", "i feel", "i struggle",
    "i prefer", "i usually", "i always", "i never",
)


def maybe_extract_memory(user_id: int, user_message: str):
    lower = user_message.lower().strip()
    if len(lower) < 10 or len(lower.split()) > 120:
        return
    if any(lower.startswith(s) or f" {s} " in f" {lower} " for s in _MEMORY_SIGNALS):
        existing = retrieve_user_memory(user_id, user_message, top_k=1)
        if existing:
            from difflib import SequenceMatcher
            if SequenceMatcher(None, existing[0].lower(), lower).ratio() > 0.75:
                return
        save_user_memory(user_id, user_message)
        print(f"🧠 Saved memory for user {user_id}: {user_message[:60]}…", flush=True)"""rag_engine.py — lightweight retrieval helpers for PartnerAI.

This version avoids heavy local embedding libraries so it can run in
serverless environments such as Vercel.
"""

import os
import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def _default_db_path() -> str:
    if os.getenv("VERCEL"):
        return os.getenv("PARTNERAI_DB_PATH", "/tmp/partnerai.db")
    return os.getenv("PARTNERAI_DB_PATH", str(Path(__file__).resolve().parent / "partnerai.db"))


DB_NAME = _default_db_path()


@contextmanager
def _get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _score_text(query: str, candidate: str) -> float:
    q_tokens = Counter(_tokenize(query))
    c_tokens = Counter(_tokenize(candidate))
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = sum(min(q_tokens[t], c_tokens[t]) for t in q_tokens if t in c_tokens)
    return overlap / max(1, len(q_tokens))


def _init_rag_tables():
    with _get_db() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memory_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                importance_score INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS domain_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_type TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """
        )
        conn.commit()


class _IndexView:
    def __init__(self):
        self.size = 0

    def reset(self):
        self.size = 0


user_memory_index = _IndexView()
domain_knowledge_index = _IndexView()


def _empty_embedding() -> bytes:
    return b""


def save_user_memory(user_id: int, text: str, importance_score: int = 1) -> int:
    now = datetime.utcnow().isoformat()
    with _get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO user_memory_vectors (user_id, content, embedding, importance_score, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, text, _empty_embedding(), importance_score, now),
        )
        conn.commit()
        row_id = c.lastrowid
    user_memory_index.size += 1
    return row_id


def retrieve_user_memory(user_id: int, query: str, top_k: int = 3) -> list[str]:
    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT content, importance_score FROM user_memory_vectors WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    scored = []
    for row in rows:
        score = _score_text(query, row["content"]) + (row["importance_score"] or 0) * 0.05
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in scored[:top_k]]


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += max(1, chunk_size - overlap)
    return chunks


def ingest_domain_file(domain_type: str, file_path: str) -> int:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Domain file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    chunks = _chunk_text(raw)
    if not chunks:
        return 0

    with _get_db() as conn:
        c = conn.cursor()
        for chunk in chunks:
            c.execute(
                "INSERT INTO domain_knowledge (domain_type, content, embedding) VALUES (?, ?, ?)",
                (domain_type, chunk, _empty_embedding()),
            )
        conn.commit()

    domain_knowledge_index.size += len(chunks)
    print(f"📚 Ingested {len(chunks)} chunks from '{file_path}' → domain '{domain_type}'", flush=True)
    return len(chunks)


def retrieve_domain_knowledge(domain_type: str, query: str, top_k: int = 3) -> list[str]:
    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT content FROM domain_knowledge WHERE domain_type = ?",
            (domain_type,),
        ).fetchall()

    scored = []
    for row in rows:
        score = _score_text(query, row["content"])
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in scored[:top_k]]


def init_rag_system():
    _init_rag_tables()
    with _get_db() as conn:
        user_count = conn.execute("SELECT COUNT(*) FROM user_memory_vectors").fetchone()[0]
        domain_count = conn.execute("SELECT COUNT(*) FROM domain_knowledge").fetchone()[0]
    user_memory_index.size = int(user_count or 0)
    domain_knowledge_index.size = int(domain_count or 0)
    print(
        f"✅ RAG system initialised (memories={user_memory_index.size}, domain={domain_knowledge_index.size})",
        flush=True,
    )


MAX_CONTEXT_WORDS = 800


def _truncate_to_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _domain_from_goal(goal: str) -> str:
    g = (goal or "").lower()
    if any(k in g for k in ("fitness", "gym", "workout", "muscle", "weight", "body")):
        return "fitness"
    if any(k in g for k in ("code", "coding", "python", "programming", "software", "developer", "web", "app")):
        return "dev"
    if any(k in g for k in ("study", "exam", "college", "university", "learn", "course")):
        return "study"
    if any(k in g for k in ("business", "startup", "entrepreneur", "freelance", "money", "income")):
        return "business"
    return "general"


def build_rag_context(user_id: int, query: str, user_goal: str = "") -> str:
    sections = []
    word_budget = MAX_CONTEXT_WORDS

    memories = retrieve_user_memory(user_id, query, top_k=3)
    if memories:
        mem_block = "RELEVANT USER MEMORY:\n" + "\n".join(f"- {m}" for m in memories)
        if len(mem_block.split()) > word_budget // 2:
            mem_block = _truncate_to_words(mem_block, word_budget // 2)
        sections.append(mem_block)
        word_budget -= len(mem_block.split())

    domain = _domain_from_goal(user_goal) if user_goal else "general"
    chunks = retrieve_domain_knowledge(domain, query, top_k=3)
    if chunks:
        dk_block = "RELEVANT DOMAIN KNOWLEDGE:\n" + "\n".join(f"- {c}" for c in chunks)
        if len(dk_block.split()) > word_budget:
            dk_block = _truncate_to_words(dk_block, word_budget)
        sections.append(dk_block)

    return "\n".join(sections)


_MEMORY_SIGNALS = (
    "i am", "i'm", "my name", "i work", "i study", "i like", "i love",
    "i hate", "i want", "i need", "i have", "i started", "i finished",
    "my goal", "my job", "my hobby", "i feel", "i struggle",
    "i prefer", "i usually", "i always", "i never",
)


def maybe_extract_memory(user_id: int, user_message: str):
    lower = user_message.lower().strip()
    if len(lower) < 10 or len(lower.split()) > 120:
        return
    if any(lower.startswith(s) or f" {s} " in f" {lower} " for s in _MEMORY_SIGNALS):
        existing = retrieve_user_memory(user_id, user_message, top_k=1)
        if existing:
            from difflib import SequenceMatcher
            if SequenceMatcher(None, existing[0].lower(), lower).ratio() > 0.75:
                return
        save_user_memory(user_id, user_message)
        print(f"🧠 Saved memory for user {user_id}: {user_message[:60]}…", flush=True)"""
rag_engine.py — Retrieval-Augmented Generation for PartnerAI

Provides:
  • User Memory RAG   — stores & retrieves per-user memories via FAISS
  • Domain Knowledge RAG — ingests .txt files, chunks them, retrieves relevant context
  • Context builder    — assembles RAG context for injection into LLM prompts

Optimised for 8 GB RAM:
  • all-MiniLM-L6-v2 (≈80 MB)  — loaded once as a singleton
  • FAISS IndexFlatL2 (dim 384) — rebuilt from SQLite on startup
  • Top-3 retrieval per category, total injection ≤ 800 words
"""

import os
import sqlite3
import struct
import time
import threading
import numpy as np
import faiss
from datetime import datetime
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Lazy / singleton embedding model  (keeps RAM usage predictable)
# ---------------------------------------------------------------------------
_model_lock = threading.Lock()
_embedding_model = None
EMBEDDING_DIM = 384


def _get_model():
    """Load sentence-transformers model once (thread-safe)."""
    global _embedding_model
    if _embedding_model is None:
        with _model_lock:
            if _embedding_model is None:  # double-check after lock
                from sentence_transformers import SentenceTransformer
                print("📦 Loading embedding model (all-MiniLM-L6-v2)…", flush=True)
                _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                print("✅ Embedding model loaded.", flush=True)
    return _embedding_model


def embed_text(text: str) -> np.ndarray:
    """Return a 384-dim float32 vector for *text*."""
    model = _get_model()
    vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype(np.float32).flatten()


def embed_texts(texts: list[str]) -> np.ndarray:
    """Batch-embed a list of strings → (N, 384) float32 array."""
    model = _get_model()
    vecs = model.encode(texts, convert_to_numpy=True,
                        normalize_embeddings=True, batch_size=64,
                        show_progress_bar=False)
    return vecs.astype(np.float32)


# ---------------------------------------------------------------------------
# Blob helpers  (float32 array ↔ bytes)
# ---------------------------------------------------------------------------

def _vec_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def _blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


# ---------------------------------------------------------------------------
# Database helpers  (reuses partnerai.db via memory.get_db)
# ---------------------------------------------------------------------------
DB_NAME = "partnerai.db"


@contextmanager
def _get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def _init_rag_tables():
    """Create the two RAG tables if they don't exist."""
    with _get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_memory_vectors (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                content          TEXT    NOT NULL,
                embedding        BLOB    NOT NULL,
                importance_score INTEGER DEFAULT 1,
                created_at       TEXT    NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS domain_knowledge (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_type  TEXT NOT NULL,
                content      TEXT NOT NULL,
                embedding    BLOB NOT NULL
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# FAISS index wrappers
# ---------------------------------------------------------------------------

class FAISSIndex:
    """Thin wrapper around a flat L2 index + an id-mapping list.

    The mapping list keeps the SQLite row-id at the same position as the
    corresponding vector in the FAISS index so we can translate FAISS
    result positions back to database rows.
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.id_map: list[int] = []          # position → SQLite row id
        self._lock = threading.Lock()

    # -- mutators ----------------------------------------------------------

    def add(self, row_id: int, vector: np.ndarray):
        vec = vector.astype(np.float32).reshape(1, self.dim)
        with self._lock:
            self.index.add(vec)
            self.id_map.append(row_id)

    def bulk_add(self, row_ids: list[int], vectors: np.ndarray):
        """Add many vectors at once (vectors shape = (N, dim))."""
        vecs = vectors.astype(np.float32)
        with self._lock:
            self.index.add(vecs)
            self.id_map.extend(row_ids)

    def reset(self):
        with self._lock:
            self.index.reset()
            self.id_map.clear()

    # -- query -------------------------------------------------------------

    def search(self, query_vec: np.ndarray, top_k: int = 3) -> list[tuple[int, float]]:
        """Return list of (row_id, distance) sorted by ascending distance."""
        if self.index.ntotal == 0:
            return []
        qv = query_vec.astype(np.float32).reshape(1, self.dim)
        k = min(top_k, self.index.ntotal)
        with self._lock:
            distances, indices = self.index.search(qv, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            results.append((self.id_map[idx], float(dist)))
        return results

    @property
    def size(self) -> int:
        return self.index.ntotal


# Global indexes
user_memory_index = FAISSIndex()
domain_knowledge_index = FAISSIndex()


# ---------------------------------------------------------------------------
# PART 1 — User Memory RAG
# ---------------------------------------------------------------------------

def save_user_memory(user_id: int, text: str, importance_score: int = 1) -> int:
    """Embed *text*, store in SQLite + FAISS.  Returns the new row id."""
    vec = embed_text(text)
    blob = _vec_to_blob(vec)
    now = datetime.utcnow().isoformat()

    with _get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO user_memory_vectors "
            "(user_id, content, embedding, importance_score, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, text, blob, importance_score, now),
        )
        conn.commit()
        row_id = c.lastrowid

    user_memory_index.add(row_id, vec)
    return row_id


def retrieve_user_memory(user_id: int, query: str, top_k: int = 3) -> list[str]:
    """Return up to *top_k* memory texts for *user_id* most relevant to *query*."""
    if user_memory_index.size == 0:
        return []

    query_vec = embed_text(query)

    # Over-fetch to compensate for filtering by user_id
    candidates = user_memory_index.search(query_vec, top_k=top_k * 5)
    if not candidates:
        return []

    row_ids = [rid for rid, _ in candidates]
    placeholders = ",".join("?" * len(row_ids))

    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT id, content FROM user_memory_vectors "
            f"WHERE id IN ({placeholders}) AND user_id = ? "
            f"ORDER BY importance_score DESC",
            (*row_ids, user_id),
        ).fetchall()

    # Re-rank by FAISS distance (preserve FAISS ordering for matched rows)
    id_to_content = {r["id"]: r["content"] for r in rows}
    results = []
    for rid, _dist in candidates:
        if rid in id_to_content:
            results.append(id_to_content[rid])
            if len(results) >= top_k:
                break
    return results


# ---------------------------------------------------------------------------
# PART 2 — Domain Knowledge RAG
# ---------------------------------------------------------------------------

def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split *text* into word-level chunks of ~*chunk_size* words with *overlap*."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest_domain_file(domain_type: str, file_path: str) -> int:
    """Read a .txt file, chunk it, embed chunks, store in SQLite + FAISS.

    Returns the number of chunks ingested.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Domain file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    chunks = _chunk_text(raw)
    if not chunks:
        return 0

    vectors = embed_texts(chunks)

    with _get_db() as conn:
        c = conn.cursor()
        row_ids = []
        for chunk, vec in zip(chunks, vectors):
            blob = _vec_to_blob(vec)
            c.execute(
                "INSERT INTO domain_knowledge (domain_type, content, embedding) "
                "VALUES (?, ?, ?)",
                (domain_type, chunk, blob),
            )
            row_ids.append(c.lastrowid)
        conn.commit()

    domain_knowledge_index.bulk_add(row_ids, vectors)
    print(f"📚 Ingested {len(chunks)} chunks from '{file_path}' → domain '{domain_type}'", flush=True)
    return len(chunks)


def retrieve_domain_knowledge(domain_type: str, query: str, top_k: int = 3) -> list[str]:
    """Return up to *top_k* domain chunks of *domain_type* relevant to *query*."""
    if domain_knowledge_index.size == 0:
        return []

    query_vec = embed_text(query)
    candidates = domain_knowledge_index.search(query_vec, top_k=top_k * 5)
    if not candidates:
        return []

    row_ids = [rid for rid, _ in candidates]
    placeholders = ",".join("?" * len(row_ids))

    with _get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT id, content FROM domain_knowledge "
            f"WHERE id IN ({placeholders}) AND domain_type = ?",
            (*row_ids, domain_type),
        ).fetchall()

    id_to_content = {r["id"]: r["content"] for r in rows}
    results = []
    for rid, _dist in candidates:
        if rid in id_to_content:
            results.append(id_to_content[rid])
            if len(results) >= top_k:
                break
    return results


# ---------------------------------------------------------------------------
# PART 3 — Startup / index rebuild
# ---------------------------------------------------------------------------

def init_rag_system():
    """Create tables and rebuild FAISS indexes from SQLite.

    Call once at server startup.
    """
    _init_rag_tables()

    t0 = time.time()

    # ── Rebuild user_memory_index ─────────────────────────────────────────
    user_memory_index.reset()
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, embedding FROM user_memory_vectors"
        ).fetchall()

    if rows:
        row_ids = [r[0] for r in rows]
        vecs = np.array([_blob_to_vec(r[1]) for r in rows], dtype=np.float32)
        user_memory_index.bulk_add(row_ids, vecs)

    # ── Rebuild domain_knowledge_index ────────────────────────────────────
    domain_knowledge_index.reset()
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, embedding FROM domain_knowledge"
        ).fetchall()

    if rows:
        row_ids = [r[0] for r in rows]
        vecs = np.array([_blob_to_vec(r[1]) for r in rows], dtype=np.float32)
        domain_knowledge_index.bulk_add(row_ids, vecs)

    elapsed = time.time() - t0
    print(
        f"✅ RAG system initialised in {elapsed:.2f}s  "
        f"(memories={user_memory_index.size}, domain={domain_knowledge_index.size})",
        flush=True,
    )


# ---------------------------------------------------------------------------
# PART 4 — Context builder  (used by the chat endpoint)
# ---------------------------------------------------------------------------

MAX_CONTEXT_WORDS = 800  # hard cap for injected context


def _truncate_to_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _domain_from_goal(goal: str) -> str:
    """Map a user's career/goal string to a domain_type key."""
    g = goal.lower()
    if any(k in g for k in ("fitness", "gym", "workout", "muscle", "weight", "body")):
        return "fitness"
    if any(k in g for k in ("code", "coding", "python", "programming", "software", "developer", "web", "app")):
        return "dev"
    if any(k in g for k in ("study", "exam", "college", "university", "learn", "course")):
        return "study"
    if any(k in g for k in ("business", "startup", "entrepreneur", "freelance", "money", "income")):
        return "business"
    return "general"


def build_rag_context(user_id: int, query: str, user_goal: str = "") -> str:
    """Retrieve memories + domain knowledge and return a formatted block.

    The result is guaranteed to be ≤ MAX_CONTEXT_WORDS words so it can be
    injected straight into the system prompt without blowing up the context
    window.
    """
    sections: list[str] = []
    word_budget = MAX_CONTEXT_WORDS

    # 1. User memories  (prioritised)
    memories = retrieve_user_memory(user_id, query, top_k=3)
    if memories:
        mem_block = "RELEVANT USER MEMORY:\n"
        for m in memories:
            mem_block += f"- {m}\n"
        mem_words = len(mem_block.split())
        if mem_words > word_budget // 2:
            mem_block = _truncate_to_words(mem_block, word_budget // 2)
        sections.append(mem_block)
        word_budget -= len(mem_block.split())

    # 2. Domain knowledge
    domain = _domain_from_goal(user_goal) if user_goal else "general"
    chunks = retrieve_domain_knowledge(domain, query, top_k=3)
    if chunks:
        dk_block = "RELEVANT DOMAIN KNOWLEDGE:\n"
        for c in chunks:
            dk_block += f"- {c}\n"
        dk_words = len(dk_block.split())
        if dk_words > word_budget:
            dk_block = _truncate_to_words(dk_block, word_budget)
        sections.append(dk_block)

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# PART 5 — Automatic memory extraction helper
# ---------------------------------------------------------------------------

# Keywords / phrases that signal a meaningful user fact worth remembering
_MEMORY_SIGNALS = (
    "i am", "i'm", "my name", "i work", "i study", "i like", "i love",
    "i hate", "i want", "i need", "i have", "i started", "i finished",
    "my goal", "my job", "my hobby", "i feel", "i struggle",
    "i prefer", "i usually", "i always", "i never",
)


def maybe_extract_memory(user_id: int, user_message: str):
    """Heuristic: if the message looks like a personal fact, save it.

    This is intentionally conservative — only fires on clear self-disclosures.
    Call this in the background so it never slows down the chat response.
    """
    lower = user_message.lower().strip()
    # Skip very short or very long messages
    if len(lower) < 10 or len(lower.split()) > 120:
        return
    if any(lower.startswith(s) or f" {s} " in f" {lower} " for s in _MEMORY_SIGNALS):
        # De-duplicate: don't save near-identical memories
        existing = retrieve_user_memory(user_id, user_message, top_k=1)
        if existing:
            from difflib import SequenceMatcher
            ratio = SequenceMatcher(None, existing[0].lower(), lower).ratio()
            if ratio > 0.75:
                return  # too similar, skip
        save_user_memory(user_id, user_message)
        print(f"🧠 Saved memory for user {user_id}: {user_message[:60]}…", flush=True)

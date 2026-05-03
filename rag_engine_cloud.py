"""rag_engine_cloud.py — lightweight retrieval helpers for PartnerAI.

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
        print(f"🧠 Saved memory for user {user_id}: {user_message[:60]}…", flush=True)

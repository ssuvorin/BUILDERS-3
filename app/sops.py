"""SOP loading and retrieval with source attribution.

Retrieval is BM25 over stemmed tokens with a coverage gate: a light suffix
stemmer folds word forms together ("checking harnesses" finds "check the
harness"), a small synonym map translates how workers talk into how SOPs
are written ("cherry picker" → MEWP), and section headings weigh double.
The gate still returns [] when the corpus doesn't cover the question —
that empty result drives the agent's escalation path, so recall must never
be bought by letting weak matches through.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from app.config import DEMO_DATA_DIR

_STOPWORDS = frozenset(
    ["a", "an", "the", "is", "are", "do", "does", "how", "what", "when", "where", "why",
     "i", "my", "me", "we", "you", "your", "it", "for", "to", "of", "in", "on", "at",
     "and", "or", "with", "be", "can", "should", "up", "this", "that",
     "will", "would", "could", "shall", "may", "might", "was", "were", "been",
     "long", "take",
     "uh", "um", "so", "like", "thing", "hey", "ok", "okay", "please", "just"]
)

# How workers say it → how the SOPs write it. Phrases are replaced in the
# raw query; single tokens are mapped after stemming.
_PHRASE_SYNONYMS = {
    "cherry picker": "mewp",
    "boom lift": "mewp",
    "man lift": "mewp",
    "scissor lift": "mewp",
}
_TOKEN_SYNONYMS = {
    "windy": "wind",
    "gusty": "gust",
    "hot": "heat",
    "temperature": "heat",
}

_BM25_K1 = 1.5
_BM25_B = 0.75
_COVERAGE_GATE = 0.3


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    doc_title: str
    filename: str
    section: str
    text: str


def _parse_frontmatter(body: str) -> tuple[dict, str]:
    if not body.startswith("---"):
        return {}, body
    parts = body.split("---", 2)
    if len(parts) < 3:
        return {}, body
    meta = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, parts[2]


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, text) sections."""
    parts = re.split(r"^(#{1,3} .+)$", body, flags=re.MULTILINE)
    sections, current = [], "Intro"
    for part in parts:
        if part.startswith("#"):
            current = part.lstrip("# ").strip()
        elif part.strip():
            sections.append((current, part.strip()))
    return sections


def load_chunks(data_dir: Path = DEMO_DATA_DIR) -> list[Chunk]:
    chunks = []
    for path in sorted(data_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        doc_id = meta.get("document_id", path.stem)
        title = meta.get("title", path.stem)
        for section, text in _split_sections(body):
            chunks.append(Chunk(doc_id, title, path.name, section, text))
    return chunks


def _stem(word: str) -> str:
    """Light suffix stemmer — folds plurals and regular verb forms."""
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 3 and word.endswith("es") and word[-3] in "sxz":
        word = word[:-2]
    elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed"):
        word = word[:-2]
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiou":
        word = word[:-1]
    return word


def _tokens(text: str) -> list[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in _STOPWORDS]


@cache
def _chunk_counts(chunk: Chunk) -> Counter:
    """Term counts for a chunk; section heading tokens weigh double.
    Cached — chunks are frozen and the counter is only ever read."""
    counts = Counter(_tokens(chunk.text))
    counts.update(_tokens(chunk.section) * 2)
    return counts


def search(query: str, chunks: list[Chunk], top_k: int = 3) -> list[dict]:
    """BM25 over stemmed tokens with a coverage gate. Returns [] when
    nothing matches so the agent can escalate instead of inventing."""
    raw = query.lower()
    for phrase, canon in _PHRASE_SYNONYMS.items():
        raw = raw.replace(phrase, canon)
    q_tokens = {_TOKEN_SYNONYMS.get(t, t) for t in _tokens(raw)}
    if not q_tokens:
        return []
    counts = [_chunk_counts(chunk) for chunk in chunks]
    lengths = [sum(c.values()) for c in counts]
    avg_len = sum(lengths) / len(lengths) if lengths else 1
    n_chunks = len(chunks)
    doc_freq = {t: sum(1 for c in counts if t in c) for t in q_tokens}
    idf = {t: math.log(1 + (n_chunks - df + 0.5) / (df + 0.5)) for t, df in doc_freq.items()}
    scored = []
    for chunk, chunk_counts, length in zip(chunks, counts, lengths):
        overlap = q_tokens & chunk_counts.keys()
        if len(overlap) / len(q_tokens) < _COVERAGE_GATE:
            continue
        norm = _BM25_K1 * (1 - _BM25_B + _BM25_B * length / avg_len)
        score = sum(
            idf[t] * chunk_counts[t] * (_BM25_K1 + 1) / (chunk_counts[t] + norm)
            for t in overlap
        )
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "source": f"{c.doc_id} — {c.doc_title}",
            "section": c.section,
            "filename": c.filename,
            "text": c.text,
            "relevance": round(score, 2),
        }
        for score, c in scored[:top_k]
    ]

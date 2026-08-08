"""SOP loading and retrieval with source attribution."""
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import DEMO_DATA_DIR

_STOPWORDS = frozenset(
    ["a", "an", "the", "is", "are", "do", "does", "how", "what", "when", "where", "why",
     "i", "my", "me", "we", "you", "your", "it", "for", "to", "of", "in", "on", "at",
     "and", "or", "with", "be", "can", "should", "up", "this", "that",
     "uh", "um", "so", "like", "thing", "hey", "ok", "okay", "please", "just"]
)


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


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


def search(query: str, chunks: list[Chunk], top_k: int = 3) -> list[dict]:
    """Keyword retrieval (coverage gate + tf/df scoring). Returns [] when
    nothing matches so the agent can refuse instead of inventing an answer."""
    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    doc_freq = {t: sum(1 for c in chunks if t in _tokens(c.text)) or 1 for t in q_tokens}
    scored = []
    for chunk in chunks:
        body = (chunk.section + " " + chunk.text).lower()
        chunk_tokens = _tokens(body)
        overlap = q_tokens & chunk_tokens
        coverage = len(overlap) / len(q_tokens)
        if coverage < 0.3:
            continue
        score = sum(body.count(t) / doc_freq[t] for t in overlap)
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

"""SOP loading, retrieval with source attribution, and threshold extraction.

Thresholds are parsed from the SOP text — never hardcoded (constitution
principle + hackathon forbidden action A7).
"""
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import DEMO_DATA_DIR

_STOPWORDS = frozenset(
    ["a", "an", "the", "is", "are", "do", "does", "how", "what", "when", "where", "why", "i", "my", "me", "we", "you", "your", "it", "for", "to", "of", "in", "on", "at", "and", "or", "with", "be", "can", "should"]
)


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    doc_title: str
    filename: str
    section: str
    text: str


@dataclass(frozen=True)
class Threshold:
    activity: str
    limit_value: float
    unit: str
    source_doc: str
    quote: str


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
        body = path.read_text(encoding="utf-8")
        title = body.splitlines()[0].lstrip("# ").strip()
        doc_id_match = re.search(r"Document:\s*(\S+)", body)
        doc_id = doc_id_match.group(1) if doc_id_match else path.stem
        for section, text in _split_sections(body):
            chunks.append(Chunk(doc_id, title, path.name, section, text))
    return chunks


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


def search(query: str, chunks: list[Chunk], top_k: int = 3) -> list[dict]:
    """Keyword-overlap retrieval. Returns [] when nothing matches so the
    agent can refuse instead of inventing an answer."""
    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    doc_freq = {t: sum(1 for c in chunks if t in _tokens(c.text)) or 1 for t in q_tokens}
    scored = []
    for chunk in chunks:
        chunk_tokens = _tokens(chunk.section + " " + chunk.text)
        overlap = q_tokens & chunk_tokens
        coverage = len(overlap) / len(q_tokens)
        if coverage < 0.3:
            continue
        score = sum(1.0 / doc_freq[t] for t in overlap)
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


_THRESHOLD_ROW = re.compile(
    r"^\|\s*(?P<activity>[^|]+?)\s*\|\s*(?P<limit>\d+(?:\.\d+)?)\s*(?P<unit>mph|km/h|°C)",
    re.MULTILINE,
)


def extract_thresholds(chunks: list[Chunk]) -> list[Threshold]:
    """Parse limit tables (e.g. wind speed rows) out of the loaded SOPs."""
    thresholds = []
    for chunk in chunks:
        for match in _THRESHOLD_ROW.finditer(chunk.text):
            activity = match.group("activity").strip()
            if activity.lower() in {"activity", "condition", "---"} or "-" == activity[0]:
                continue
            thresholds.append(
                Threshold(
                    activity=activity,
                    limit_value=float(match.group("limit")),
                    unit=match.group("unit"),
                    source_doc=f"{chunk.doc_id} — {chunk.doc_title}",
                    quote=match.group(0).strip("| "),
                )
            )
    return thresholds


def match_threshold(activity_query: str, thresholds: list[Threshold]) -> Threshold | None:
    q_tokens = _tokens(activity_query)
    best, best_score = None, 0.0
    for t in thresholds:
        if t.unit not in ("mph", "km/h"):
            continue
        score = len(q_tokens & _tokens(t.activity))
        if score > best_score:
            best, best_score = t, score
    if best is None:
        wind = [t for t in thresholds if t.unit in ("mph", "km/h")]
        best = wind[0] if wind else None
    return best

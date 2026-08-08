"""Question log → learn list.

Every question already flows through the tool endpoints, so the backend
counts them: which topics get asked most (onboarding / toolbox-talk
material) and which questions no SOP covers (documentation gaps).

In-memory by default, consistent with the demo's no-persistence scope.
Set ASK_LOG_PATH to a JSONL file to survive restarts.
"""
import json
import logging
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger("heatsafe.asklog")

ASK_LOG_PATH = os.getenv("ASK_LOG_PATH", "")
_MAX_RECORDS = int(os.getenv("ASK_LOG_MAX_RECORDS", "10000"))

_records: list[dict] = []


def _load() -> None:
    path = Path(ASK_LOG_PATH) if ASK_LOG_PATH else None
    if not path or not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                _records.append(json.loads(line))
            except ValueError:
                logger.warning("ask log: skipping corrupt line in %s", path)
    del _records[:-_MAX_RECORDS]


def record(kind: str, question: str, topic: str | None, covered: bool) -> None:
    """kind: "procedure" (search_sops) or "conditions" (check_weather)."""
    entry = {
        "ts": time.time(),
        "kind": kind,
        "question": question.strip(),
        "topic": topic,
        "covered": covered,
    }
    _records.append(entry)
    del _records[:-_MAX_RECORDS]
    if ASK_LOG_PATH:
        with Path(ASK_LOG_PATH).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def learn_list(top_k: int = 10) -> dict:
    """Aggregate the log into a supervisor-facing learn list."""
    topic_counts: Counter[str] = Counter()
    topic_samples: dict[str, list[str]] = defaultdict(list)
    gap_counts: Counter[str] = Counter()
    for entry in _records:
        if entry["covered"] and entry["topic"]:
            topic_counts[entry["topic"]] += 1
            samples = topic_samples[entry["topic"]]
            if entry["question"] not in samples and len(samples) < 3:
                samples.append(entry["question"])
        elif not entry["covered"] and entry["kind"] == "procedure":
            # a weather-source outage is not a documentation gap
            gap_counts[entry["question"].lower()] += 1
    return {
        "total_questions": len(_records),
        "top_topics": [
            {"topic": topic, "count": count, "sample_questions": topic_samples[topic]}
            for topic, count in topic_counts.most_common(top_k)
        ],
        "coverage_gaps": [
            {"question": q, "count": count} for q, count in gap_counts.most_common(top_k)
        ],
        "guidance": "Top topics are what the crew asks most — use them for onboarding "
        "and toolbox talks. Coverage gaps are questions no company document answers — "
        "candidates for new SOP sections.",
    }


def reset() -> None:
    _records.clear()


_load()

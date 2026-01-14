import json
from pathlib import Path
from collections import defaultdict

MEMORY_FILE = Path("rewrite_memory.json")


def load_rewrite_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return []


def analyze_rewrites():
    memory = load_rewrite_memory()

    bullet_stats = defaultdict(lambda: {
        "count": 0,
        "avg_delta": 0.0,
        "positive": 0,
        "negative": 0
    })

    for r in memory:
        key = f"exp_{r['experience_index']}_bullet_{r['bullet_index']}"
        delta = r.get("delta", 0.0)

        stats = bullet_stats[key]
        stats["count"] += 1
        stats["avg_delta"] += delta

        if delta > 0:
            stats["positive"] += 1
        elif delta < 0:
            stats["negative"] += 1

    for stats in bullet_stats.values():
        if stats["count"] > 0:
            stats["avg_delta"] /= stats["count"]

    ranked = sorted(
        bullet_stats.items(),
        key=lambda x: x[1]["avg_delta"],
        reverse=True
    )

    return [
        {
            "bullet_key": k,
            **v
        }
        for k, v in ranked
    ]
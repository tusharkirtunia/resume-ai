import json
import os
from collections import defaultdict

MEMORY_FILE = "bullet_memory.json"


class BulletMemory:
    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        self.memory = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return defaultdict(lambda: {
                "attempts": 0,
                "successes": 0,
                "avg_delta": 0.0
            })

        with open(self.path, "r") as f:
            raw = json.load(f)

        mem = defaultdict(lambda: {
            "attempts": 0,
            "successes": 0,
            "avg_delta": 0.0
        })

        for k, v in raw.items():
            mem[k] = v

        return mem

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def _key(self, old: str, new: str):
        return f"{old.strip()} -> {new.strip()}"

    def record(self, old: str, new: str, delta: float):
        key = self._key(old, new)
        entry = self.memory[key]

        entry["attempts"] += 1
        if delta > 0:
            entry["successes"] += 1

        # incremental mean
        prev_avg = entry["avg_delta"]
        n = entry["attempts"]
        entry["avg_delta"] = prev_avg + (delta - prev_avg) / n

        self.save()

    def score_bias(self, old: str, new: str) -> float:
        key = self._key(old, new)
        entry = self.memory.get(key)

        if not entry or entry["attempts"] < 3:
            return 0.0

        success_rate = entry["successes"] / entry["attempts"]
        return entry["avg_delta"] * success_rate
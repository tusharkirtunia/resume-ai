import json
import os
import re
from collections import defaultdict
from typing import Dict, Any, List, Tuple


class BulletMemory:
    def __init__(self, path: str = "bullet_memory.json"):
        self.path = path
        self.data = defaultdict(lambda: {"score": 0.0, "count": 0})
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                raw = json.load(f)
                for k, v in raw.items():
                    self.data[k] = v

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def _pattern(self, before: str, after: str) -> str:
        if len(after) > len(before):
            return "expand"
        if "%" in after or any(ch.isdigit() for ch in after):
            return "quantify"
        if re.search(r"\b(led|owned|designed|built)\b", after.lower()):
            return "leadership"
        return "rewrite"

    def record(self, before: str, after: str, delta: float):
        key = self._pattern(before, after)
        entry = self.data[key]
        entry["score"] += delta
        entry["count"] += 1
        self._save()

    def score_bias(self, before: str, after: str) -> float:
        key = self._pattern(before, after)
        entry = self.data.get(key)
        if not entry or entry["count"] == 0:
            return 0.0
        return entry["score"] / entry["count"]


class AutoImprover:
    def __init__(
        self,
        memory: BulletMemory,
        min_delta: float = 0.01,
        max_stagnant_iters: int = 2,
        cooldown_iters: int = 2,
    ):
        self.memory = memory
        self.min_delta = min_delta
        self.max_stagnant_iters = max_stagnant_iters
        self.cooldown_iters = cooldown_iters

        self._cooldowns = defaultdict(int)
        self._impact_cache = {}

    def _cooldown_tick(self):
        for k in list(self._cooldowns.keys()):
            self._cooldowns[k] -= 1
            if self._cooldowns[k] <= 0:
                del self._cooldowns[k]

    def _rank_bullets(self, bullets: List[str], score_fn, job: str) -> List[int]:
        cache_key = tuple(bullets)
        if cache_key in self._impact_cache:
            return self._impact_cache[cache_key]

        base_score = score_fn(bullets, job)
        impacts = []

        for idx in range(len(bullets)):
            temp_bullets = bullets[:idx] + bullets[idx + 1 :]
            temp_score = score_fn(temp_bullets, job)
            impact = base_score - temp_score
            impacts.append((impact, idx))

        impacts.sort(reverse=True, key=lambda x: x[0])
        ranked_indices = [idx for _, idx in impacts]

        self._impact_cache[cache_key] = ranked_indices
        return ranked_indices

    def improve(
        self,
        bullets: List[str],
        rewrite_fn,
        score_fn,
        job: str,
        max_iters: int = 5,
    ) -> Dict[str, Any]:

        history: List[Dict[str, Any]] = []
        stagnant_iters = 0
        best_score = score_fn(bullets, job)

        for iteration in range(1, max_iters + 1):
            self._cooldown_tick()
            improved = False

            ranked_indices = self._rank_bullets(bullets, score_fn, job)
            for idx in ranked_indices:
                if idx in self._cooldowns:
                    continue

                bullet = bullets[idx]
                rewritten = rewrite_fn(bullet, job)
                new_bullets = bullets.copy()
                new_bullets[idx] = rewritten

                new_score = score_fn(new_bullets, job)
                delta = new_score - best_score

                bias = self.memory.score_bias(bullet, rewritten)
                effective_delta = delta + bias

                if effective_delta >= self.min_delta:
                    bullets[idx] = rewritten
                    self._impact_cache.clear()
                    best_score = new_score
                    improved = True

                    self.memory.record(bullet, rewritten, delta)
                    self._cooldowns[idx] = self.cooldown_iters

                    history.append(
                        {
                            "iteration": iteration,
                            "bullet_index": idx,
                            "old": bullet,
                            "new": rewritten,
                            "score": new_score,
                            "delta": delta,
                        }
                    )
                    break

            if not improved:
                stagnant_iters += 1
                if stagnant_iters >= self.max_stagnant_iters:
                    break
            else:
                stagnant_iters = 0

        return {
            "final_score": best_score,
            "iterations_run": iteration,
            "history": history,
        }
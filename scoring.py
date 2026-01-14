import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from cache import LRUCache

model = SentenceTransformer("all-MiniLM-L6-v2")
_score_cache = LRUCache(max_size=512)
_impact_cache = LRUCache(max_size=512)

import hashlib

def stable_hash(obj) -> str:
    """
    Deterministic hash for nested resume/job structures.
    Used for caching only. Must never mutate input.
    """
    serialized = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def normalize_job(job: str) -> str:
    normalized = job.strip()
    if not normalized:
        raise ValueError("Job description must not be empty or whitespace only.")
    return normalized

def validate_resume_shape(resume: dict):
    if not isinstance(resume, dict):
        raise ValueError("Resume must be a dictionary.")
    experience = resume.get("experience", [])
    if not isinstance(experience, list):
        raise ValueError("Resume 'experience' must be a list.")
    for exp in experience:
        bullets = exp.get("bullets", [])
        if not isinstance(bullets, list):
            raise ValueError("Each 'bullets' must be a list.")
        for bullet in bullets:
            if not isinstance(bullet, str):
                raise ValueError("Each bullet must be a string.")

def resume_text(resume: dict) -> str:
    validate_resume_shape(resume)
    chunks = []
    for exp in resume.get("experience", []):
        for bullet in exp.get("bullets", []):
            if bullet.strip():
                chunks.append(bullet)
    return " ".join(chunks)


def embed(text: str):
    return model.encode([text])[0]


def _score_resume_uncached(resume: dict, job: str) -> float:
    r = embed(resume_text(resume))
    j = embed(job)
    return float(cosine_similarity([r], [j])[0][0])

def score_resume(resume: dict, job: str) -> float:
    normalized_job = normalize_job(job)
    key = ("score", stable_hash(resume), normalized_job)

    cached = _score_cache.get(key)
    if cached is not None:
        return cached

    result = _score_resume_uncached(resume, normalized_job)
    _score_cache.set(key, result)
    return result

def _bullet_impact_scores_uncached(resume: dict, job: str):
    normalized_job = normalize_job(job)
    validate_resume_shape(resume)
    """
    Returns per-bullet contribution score by measuring
    score drop when the bullet is removed.
    """
    base_score = score_resume(resume, normalized_job)
    impacts = []

    for exp_i, exp in enumerate(resume.get("experience", [])):
        for b_i, bullet in enumerate(exp.get("bullets", [])):
            if not bullet.strip():
                continue
            modified = json.loads(json.dumps(resume))
            modified["experience"][exp_i]["bullets"].pop(b_i)

            new_score = score_resume(modified, normalized_job)
            impact = base_score - new_score

            impacts.append({
                "experience_index": exp_i,
                "bullet_index": b_i,
                "bullet": bullet,
                "impact": impact
            })

    return impacts

def bullet_impact_scores(resume: dict, job: str):
    normalized_job = normalize_job(job)
    key = ("impact", stable_hash(resume), normalized_job)

    cached = _impact_cache.get(key)
    if cached is not None:
        return cached

    result = _bullet_impact_scores_uncached(resume, normalized_job)
    _impact_cache.set(key, result)
    return result

def classify_bullet_impacts(impacts, keep_threshold=0.1, rewrite_threshold=0.01):
    decisions = []

    for item in impacts:
        impact = item["impact"]

        if impact >= keep_threshold:
            action = "KEEP"
        elif impact >= rewrite_threshold:
            action = "REWRITE"
        else:
            action = "REMOVE"

        decisions.append({
            **item,
            "action": action
        })

    return decisions

def bullet_decisions(resume: dict, job: str, keep_threshold=0.1, rewrite_threshold=0.01):
    normalized_job = normalize_job(job)
    impacts = bullet_impact_scores(resume, normalized_job)
    decisions = classify_bullet_impacts(impacts, keep_threshold=keep_threshold, rewrite_threshold=rewrite_threshold)
    return decisions

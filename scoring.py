import copy
import math
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text: str) -> list[str]:
    return [
        w.lower()
        for w in text.split()
        if w.isalpha() and w.lower() not in ENGLISH_STOP_WORDS
    ]


# ---------------------------------------------------------
# RESUME VALIDATION (PURE)
# ---------------------------------------------------------

def validate_resume_shape(resume: dict):
    if not isinstance(resume, dict):
        raise ValueError("Resume must be a dict")

    experience = resume.get("experience", [])
    if not isinstance(experience, list):
        raise ValueError("experience must be a list")

    for exp in experience:
        bullets = exp.get("bullets", [])
        if not isinstance(bullets, list):
            raise ValueError("bullets must be a list")
        for b in bullets:
            if not isinstance(b, str):
                raise ValueError("bullet must be a string")


# ---------------------------------------------------------
# CORE SCORING (PURE, IMMUTABLE)
# ---------------------------------------------------------

def score_resume(resume: dict, job: str) -> float:
    validate_resume_shape(resume)

    job_tokens = normalize_text(job)
    if not job_tokens:
        return 0.0

    bullets = []
    for exp in resume.get("experience", []):
        bullets.extend(exp.get("bullets", []))

    bullet_tokens = [normalize_text(b) for b in bullets if b.strip()]
    if not bullet_tokens:
        return 0.0

    bm25 = BM25Okapi(bullet_tokens)
    scores = bm25.get_scores(job_tokens)

    if not scores.any():
        return 0.0

    return float(scores.mean())


# ---------------------------------------------------------
# BULLET-LEVEL IMPACT (PURE)
# ---------------------------------------------------------

def bullet_impact_scores(resume: dict, job: str):
    validate_resume_shape(resume)

    job_tokens = normalize_text(job)
    if not job_tokens:
        return []

    impacts = []

    for exp_i, exp in enumerate(resume.get("experience", [])):
        bullets = exp.get("bullets", [])
        tokenized = [normalize_text(b) for b in bullets if b.strip()]

        if not tokenized:
            continue

        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(job_tokens)

        for b_i, (bullet, score) in enumerate(zip(bullets, scores)):
            if not bullet.strip():
                continue

            impacts.append({
                "experience_index": exp_i,
                "bullet_index": b_i,
                "bullet": bullet,
                "impact": float(score)
            })

    return impacts
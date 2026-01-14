import re
from collections import Counter

# -----------------------------
# CONFIG
# -----------------------------

STOPWORDS = {
    "the", "and", "to", "of", "a", "in", "for", "with", "on", "by",
    "is", "as", "at", "an", "be", "this", "that"
}

BOOST_KEYWORDS = {
    "api", "apis", "backend", "performance", "latency",
    "scalable", "scalability", "design", "engineer",
    "system", "distributed", "service", "services"
}

ACTION_VERBS = {
    "built", "designed", "implemented", "optimized",
    "developed", "created", "improved", "led"
}

# -----------------------------
# UTILITIES
# -----------------------------

def tokenize(text: str):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [w for w in words if w not in STOPWORDS]

def normalize_score(value, max_value):
    if max_value == 0:
        return 0.0
    return min(value / max_value, 1.0)

# -----------------------------
# CORE SCORING
# -----------------------------

def score_resume(resume: dict, job: str) -> float:
    job_tokens = tokenize(job)
    if not job_tokens:
        return 0.0

    job_counts = Counter(job_tokens)
    total_score = 0.0
    bullets_seen = 0

    for exp in resume.get("experience", []):
        for bullet in exp.get("bullets", []):
            score = score_bullet(bullet, job_counts)
            total_score += score
            bullets_seen += 1

    if bullets_seen == 0:
        return 0.0

    return normalize_score(total_score, bullets_seen)

def score_bullet(bullet: str, job_counts: Counter) -> float:
    bullet_tokens = tokenize(bullet)
    if not bullet_tokens:
        return 0.0

    bullet_counts = Counter(bullet_tokens)

    # Base overlap
    overlap = sum(
        min(bullet_counts[t], job_counts.get(t, 0))
        for t in bullet_counts
    )

    # Keyword boosts
    boost = sum(1 for t in bullet_tokens if t in BOOST_KEYWORDS)
    action_boost = sum(1 for t in bullet_tokens if t in ACTION_VERBS)

    raw_score = overlap + (0.5 * boost) + (0.3 * action_boost)

    return normalize_score(raw_score, len(bullet_tokens))

# -----------------------------
# BULLET IMPACT
# -----------------------------

def bullet_impact_scores(resume: dict, job: str):
    job_tokens = tokenize(job)
    job_counts = Counter(job_tokens)

    impacts = []

    for exp_i, exp in enumerate(resume.get("experience", [])):
        for b_i, bullet in enumerate(exp.get("bullets", [])):
            impact = score_bullet(bullet, job_counts)
            impacts.append({
                "experience_index": exp_i,
                "bullet_index": b_i,
                "bullet": bullet,
                "impact": impact
            })

    return impacts
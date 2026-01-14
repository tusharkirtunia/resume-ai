import copy
from typing import List

from scoring import score_resume

# -----------------------------
# Variant Generation (offline)
# -----------------------------

def generate_variants(bullet: str, job: str) -> List[str]:
    """
    Simple deterministic variants.
    Intentionally cheap and offline.
    """
    if not bullet:
        return [bullet]

    return [
        bullet,
        f"Improved {bullet} with focus on {job}",
        f"{bullet} emphasizing {job}",
        f"{job} related: {bullet}",
    ]


# -----------------------------
# Scoring Helpers
# -----------------------------

def score_resume_text(text: str, job: str) -> float:
    """
    Scores a single bullet by wrapping it into a minimal resume.
    """
    temp_resume = {
        "summary": "",
        "experience": [
            {"bullets": [text]}
        ]
    }
    return score_resume(temp_resume, job)


# -----------------------------
# Phase 13.5 — Single-Pass Improvement
# -----------------------------

def auto_improve_once(resume: dict, job: str) -> dict:
    """
    Improves each bullet exactly once by choosing
    the highest scoring variant.
    """
    improved = copy.deepcopy(resume)

    for exp in improved.get("experience", []):
        bullets = exp.get("bullets", [])
        for i, old_bullet in enumerate(bullets):
            candidates = generate_variants(old_bullet, job)

            best_bullet = old_bullet
            best_score = score_resume_text(old_bullet, job)

            for c in candidates:
                s = score_resume_text(c, job)
                if s > best_score:
                    best_score = s
                    best_bullet = c

            bullets[i] = best_bullet

    return improved


# -----------------------------
# Phase 13.6 — Convergence Loop
# -----------------------------

def auto_improve_until_converged(
    resume: dict,
    job: str,
    max_iterations: int = 5,
    min_delta: float = 0.01
) -> dict:
    """
    Re-runs auto_improve_once until the score stops improving.
    """
    current = copy.deepcopy(resume)
    prev_score = score_resume(current, job)

    for _ in range(max_iterations):
        candidate = auto_improve_once(current, job)
        new_score = score_resume(candidate, job)

        if new_score - prev_score < min_delta:
            break

        current = candidate
        prev_score = new_score

    return current


# -----------------------------
# Phase 13.7 — Guardrails + Audit
# -----------------------------

def diff_bullets(original: dict, improved: dict) -> list[dict]:
    """
    Compares bullets positionally and returns a list of changes.
    """
    changes = []
    orig_exps = original.get("experience", [])
    imp_exps = improved.get("experience", [])
    max_exp_len = max(len(orig_exps), len(imp_exps))

    for exp_idx in range(max_exp_len):
        orig_exp = orig_exps[exp_idx] if exp_idx < len(orig_exps) else {}
        imp_exp = imp_exps[exp_idx] if exp_idx < len(imp_exps) else {}

        orig_bullets = orig_exp.get("bullets", [])
        imp_bullets = imp_exp.get("bullets", [])
        max_bul_len = max(len(orig_bullets), len(imp_bullets))

        for bullet_idx in range(max_bul_len):
            before = orig_bullets[bullet_idx] if bullet_idx < len(orig_bullets) else None
            after = imp_bullets[bullet_idx] if bullet_idx < len(imp_bullets) else None

            if before != after:
                changes.append({
                    "experience_index": exp_idx,
                    "bullet_index": bullet_idx,
                    "before": before,
                    "after": after
                })
    return changes


def auto_improve_with_guardrails(
    resume: dict,
    job: str,
    max_iterations: int = 5,
    min_delta: float = 0.01,
    min_total_gain: float = 0.05
) -> dict:
    """
    Runs iterative improvement but only accepts the result
    if the total score gain crosses a minimum threshold.
    Otherwise, rolls back to the original resume.
    """
    original = copy.deepcopy(resume)
    original_score = score_resume(original, job)

    improved = auto_improve_until_converged(
        resume,
        job,
        max_iterations=max_iterations,
        min_delta=min_delta
    )

    improved_score = score_resume(improved, job)

    if improved_score - original_score >= min_total_gain:
        return improved

    return original


def auto_improve_with_audit(
    resume: dict,
    job: str,
    max_iterations: int = 5,
    min_delta: float = 0.01,
    min_total_gain: float = 0.05
) -> dict:
    """
    Runs guarded improvement and returns the improved resume with an audit log.
    """
    original = copy.deepcopy(resume)
    original_score = score_resume(original, job)

    improved = auto_improve_with_guardrails(
        resume,
        job,
        max_iterations=max_iterations,
        min_delta=min_delta,
        min_total_gain=min_total_gain
    )

    improved_score = score_resume(improved, job)
    delta = improved_score - original_score
    accepted = delta >= min_total_gain

    changes = diff_bullets(original, improved)

    audit = {
        "original_score": original_score,
        "final_score": improved_score,
        "delta": delta,
        "accepted": accepted,
        "changes": changes
    }

    return {
        "resume": improved,
        "audit": audit
    }
# -----------------------------
# Phase 14.1 — Section Scoring
# -----------------------------

from scoring import score_resume
def score_summary(summary: str, job: str) -> float:
    """
    Scores only the summary section.
    """
    temp_resume = {
        "summary": summary,
        "experience": []
    }
    return score_resume(temp_resume, job)


def score_experience_block(exp: dict, job: str) -> float:
    """
    Scores a single experience block as a unit.
    """
    temp_resume = {
        "summary": "",
        "experience": [exp]
    }
    return score_resume(temp_resume, job)


def score_bullet(bullet: str, job: str) -> float:
    """
    Scores a single bullet in isolation.
    """
    temp_resume = {
        "summary": "",
        "experience": [
            {"bullets": [bullet]}
        ]
    }
    return score_resume(temp_resume, job)


def score_resume_sections(resume: dict, job: str) -> dict:
    """
    Returns a detailed section-level score map.
    """
    result = {
        "summary_score": 0.0,
        "experience_scores": [],
        "overall_score": 0.0
    }

    # Summary
    summary = resume.get("summary", "")
    if summary.strip():
        result["summary_score"] = score_summary(summary, job)

    # Experience blocks
    for exp_idx, exp in enumerate(resume.get("experience", [])):
        bullets = exp.get("bullets", [])

        bullet_scores = []
        for bullet_idx, bullet in enumerate(bullets):
            s = score_bullet(bullet, job)
            bullet_scores.append({
                "bullet_index": bullet_idx,
                "text": bullet,
                "score": s
            })

        exp_score = score_experience_block(exp, job)

        result["experience_scores"].append({
            "experience_index": exp_idx,
            "experience_score": exp_score,
            "bullets": bullet_scores
        })

    # Overall (existing logic)
    result["overall_score"] = score_resume(resume, job)

    return result
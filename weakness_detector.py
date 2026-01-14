# --------------------------------
# Phase 14.2 — Weakness Detection
# --------------------------------

from section_scoring import score_resume_sections


def detect_weaknesses(resume: dict, job: str, threshold: float = 0.3) -> dict:
    """
    Identifies weak resume components based on section-level scores.

    threshold:
        Scores below this value are considered weak.
    """

    scores = score_resume_sections(resume, job)

    weaknesses = {
        "weak_summary": None,
        "weak_experiences": [],
        "weak_bullets": []
    }

    # Summary weakness
    if scores["summary_score"] > 0 and scores["summary_score"] < threshold:
        weaknesses["weak_summary"] = {
            "score": scores["summary_score"],
            "text": resume.get("summary", "")
        }

    # Experience and bullet weaknesses
    for exp in scores["experience_scores"]:
        exp_idx = exp["experience_index"]

        # Weak experience block
        if exp["experience_score"] < threshold:
            weaknesses["weak_experiences"].append({
                "experience_index": exp_idx,
                "score": exp["experience_score"]
            })

        # Weak bullets
        for bullet in exp["bullets"]:
            if bullet["score"] < threshold:
                weaknesses["weak_bullets"].append({
                    "experience_index": exp_idx,
                    "bullet_index": bullet["bullet_index"],
                    "score": bullet["score"],
                    "text": bullet["text"]
                })

    # Rank bullets by weakness (lowest score first)
    weaknesses["weak_bullets"].sort(key=lambda x: x["score"])

    return weaknesses
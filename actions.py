import copy
from collections import defaultdict


def apply_bullet_decisions(resume: dict, decisions: list[dict]) -> dict:
    """
    Applies KEEP / REMOVE / REWRITE decisions to a resume.
    Operates on a deep copy. Deterministic. No side effects.
    """

    if not isinstance(resume, dict) or not isinstance(decisions, list):
        return resume

    new_resume = copy.deepcopy(resume)

    # Group decisions by experience index
    grouped = defaultdict(list)
    for d in decisions:
        try:
            grouped[d["experience_index"]].append(d)
        except KeyError:
            continue

    for exp_index, decs in grouped.items():
        experience = new_resume.get("experience", [])
        if exp_index < 0 or exp_index >= len(experience):
            continue

        bullets = experience[exp_index].get("bullets", [])

        # Apply in descending bullet index order to avoid shifting bugs
        decs_sorted = sorted(decs, key=lambda x: x["bullet_index"], reverse=True)

        for d in decs_sorted:
            try:
                b_index = d["bullet_index"]
                action = d["action"]
            except KeyError:
                continue

            if b_index < 0 or b_index >= len(bullets):
                continue

            if action == "KEEP":
                continue

            elif action == "REMOVE":
                bullets.pop(b_index)

            elif action == "REWRITE":
                original = bullets[b_index]
                bullets[b_index] = f"[OPTIMIZED] {original}"

            # Unknown actions are ignored silently

        experience[exp_index]["bullets"] = bullets

    return new_resume
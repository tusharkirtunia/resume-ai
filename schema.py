def validate_resume(resume):
    if not isinstance(resume, dict):
        return False

    if not isinstance(resume.get("id"), str):
        return False

    if not isinstance(resume.get("summary"), str):
        return False

    experience = resume.get("experience")
    if not isinstance(experience, list):
        return False

    for exp in experience:
        if not isinstance(exp, dict):
            return False

        if not isinstance(exp.get("id"), str):
            return False

        if not isinstance(exp.get("role"), str):
            return False

        if not isinstance(exp.get("company"), str):
            return False

        bullets = exp.get("bullets")
        if not isinstance(bullets, list):
            return False

        for b in bullets:
            if not isinstance(b, str):
                return False

    return True


def validate_state(state):
    if not isinstance(state, dict):
        return False

    active = state.get("active_variant")
    variants = state.get("variants")

    if not isinstance(active, str):
        return False

    if not isinstance(variants, dict):
        return False

    if active not in variants:
        return False

    for name, resume in variants.items():
        if not isinstance(name, str):
            return False
        if not validate_resume(resume):
            return False

    return True
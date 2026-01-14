def rewrite_bullet(bullet: str, job: str, variant: str = "default") -> str:
    bullet = bullet.strip()
    job = job.strip().lower()

    if variant == "concise":
        return f"{bullet.split('.')[0]}."

    if variant == "detailed":
        return (
            f"{bullet} while collaborating cross-functionally, "
            f"ensuring scalability, reliability, and alignment with {job} requirements."
        )

    if variant == "impactful":
        return (
            f"{bullet}, delivering measurable business impact "
            f"and directly supporting {job} objectives."
        )

    # default / fallback
    return f"{bullet} with focus on {job}"
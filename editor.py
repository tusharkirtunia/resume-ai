def update_bullet(resume, exp_index, bullet_index, new_text):
    try:
        resume["experience"][exp_index]["bullets"][bullet_index] = new_text
        return resume
    except (IndexError, KeyError, TypeError):
        return None
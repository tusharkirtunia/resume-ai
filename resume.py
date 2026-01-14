from storage import load_state, save_state


DEFAULT_RESUME = {
    "id": "base",
    "summary": "Backend developer",
    "experience": [
        {
            "id": "exp1",
            "role": "Software Engineer",
            "company": "Company A",
            "bullets": [
                "Built APIs using Python",
                "Improved performance by 30%"
            ]
        }
    ]
}


def get_resume():
    state = load_state()
    if state is None:
        save_state(DEFAULT_RESUME)
        return DEFAULT_RESUME

    return state
import copy
from scoring import score_resume, bullet_impact_scores


def test_empty_experience(job):
    resume = {
        "summary": "Test",
        "experience": []
    }

    score = score_resume(resume, job)
    assert 0.0 <= score <= 1.0


def test_missing_bullets(job):
    resume = {
        "summary": "Test",
        "experience": [{"company": "X"}]
    }

    score = score_resume(resume, job)
    assert 0.0 <= score <= 1.0


def test_empty_bullet_strings(sample_resume, job):
    resume = copy.deepcopy(sample_resume)
    resume["experience"][0]["bullets"].append("")

    impacts = bullet_impact_scores(resume, job)

    # Empty bullets should be ignored or near-zero impact
    assert all(i["impact"] >= 0 for i in impacts)
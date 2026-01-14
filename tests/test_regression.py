from scoring import score_resume, bullet_impact_scores


def test_score_regression(sample_resume, job):
    score = score_resume(sample_resume, job)

    # Regression window, not exact match
    assert 0.0 <= score <= 1.0
    assert score > 0.05


def test_impact_ordering_regression(sample_resume, job):
    impacts = bullet_impact_scores(sample_resume, job)

    assert len(impacts) == 2

    # Higher-impact bullet should stay dominant
    assert impacts[0]["impact"] >= impacts[1]["impact"]
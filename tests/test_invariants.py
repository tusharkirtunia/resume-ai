from copy import deepcopy
from scoring import score_resume, bullet_impact_scores
from main import make_bullet_decisions

def test_scoring_is_pure(sample_resume, job):
    before = deepcopy(sample_resume)
    score_resume(sample_resume, job)
    assert sample_resume == before

def test_impact_is_pure(sample_resume, job):
    before = deepcopy(sample_resume)
    bullet_impact_scores(sample_resume, job)
    assert sample_resume == before
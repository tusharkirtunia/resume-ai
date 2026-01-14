import sys
from pathlib import Path
import pytest
import copy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def job():
    return "Backend engineer with API design and performance experience"


@pytest.fixture
def sample_resume():
    return {
        "id": "base",
        "summary": "Backend developer",
        "experience": [
            {
                "id": "exp1",
                "company": "Company A",
                "role": "Software Engineer",
                "bullets": [
                    "Built APIs using Node.js",
                    "Improved performance by 30%"
                ]
            }
        ]
    }


@pytest.fixture
def frozen_resume(sample_resume):
    # Utility fixture for purity tests
    return copy.deepcopy(sample_resume)
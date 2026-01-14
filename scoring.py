# scoring.py
from openai import OpenAI
import math
import os

def get_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

def embed(text: str) -> list[float]:
    client = get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x*x for x in a))
    mag_b = math.sqrt(sum(x*x for x in b))
    return dot / (mag_a * mag_b)


def resume_text(resume: dict) -> str:
    chunks = []
    for exp in resume.get("experience", []):
        chunks.extend(exp.get("bullets", []))
    return " ".join(chunks)


def score_resume(resume: dict, job: str) -> float:
    resume_emb = embed(resume_text(resume))
    job_emb = embed(job)
    return cosine(resume_emb, job_emb)

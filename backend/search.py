from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Candidate, Job, JobCandidateVector


def embed_job(_job: Job) -> list[float]:
    return [1.0, 0.0, 0.0, 0.0]


def semantic_search(session: Session, job: Job, limit: int = 6) -> list[dict]:
    job_embedding = embed_job(job)
    similarity = (1 - JobCandidateVector.embedding.cosine_distance(job_embedding)).label(
        "vector_similarity"
    )

    query = (
        select(Candidate, similarity)
        .join(JobCandidateVector, JobCandidateVector.candidate_id == Candidate.id)
        .where(JobCandidateVector.job_id == job.id)
        .order_by(similarity.desc())
        .limit(limit)
    )
    rows = session.execute(query).all()
    return [{"candidate": row[0], "vector_similarity": float(row[1])} for row in rows]

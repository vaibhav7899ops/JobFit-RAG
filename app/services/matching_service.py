from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.chroma import jobs_collection
from app.models.match import Match
from app.models.user import User
from app.core.config import MATCH_TOP_K
from app.schemas.match import MatchAnalysis, MatchCreate
from app.services.embedding_service import embed_text
from app.services.groq_client import analyze_resume_against_jobs
from app.services.match_service import (
    create_match,
    get_current_matches_for_user,
    get_jobs_by_ids,
    get_latest_job_sync_time,
    get_latest_resume,
)


def _matches_are_fresh(matches: list[Match], resume_uploaded_at: datetime, latest_job_sync: datetime) -> bool:
    calculated_at = matches[0].calculated_at
    return calculated_at > resume_uploaded_at and calculated_at > latest_job_sync


def _retrieve_candidate_jobs(db: Session, resume_text: str) -> list[dict]:
    resume_embedding = embed_text(resume_text)
    results = jobs_collection.query(query_embeddings=[resume_embedding], n_results=MATCH_TOP_K)
    job_ids = [int(job_id) for job_id in results["ids"][0]]

    jobs = get_jobs_by_ids(db, job_ids)
    return [
        {"id": job.id, "title": job.title, "company": job.company, "description": job.description}
        for job in jobs
    ]


def _recompute_matches(db: Session, user: User, resume_text: str) -> list[Match]:
    candidate_jobs = _retrieve_candidate_jobs(db, resume_text)
    batch_response = analyze_resume_against_jobs(resume_text, candidate_jobs)

    batch_timestamp = datetime.now(timezone.utc)
    new_matches = []
    for analysis in batch_response.analyses:
        match_data = MatchCreate(
            user_id=user.id,
            job_id=analysis.job_id,
            score=analysis.score,
            analysis_json=MatchAnalysis(
                matching_skills=analysis.matching_skills,
                missing_skills=analysis.missing_skills,
                summary=analysis.summary,
            ),
        )
        new_matches.append(create_match(db, match_data, batch_timestamp))

    return new_matches


def get_matches_for_user(db: Session, user: User) -> list[Match]:
    latest_resume = get_latest_resume(db, user.id)
    if latest_resume is None:
        raise ValueError("Upload a resume before requesting matches")

    latest_job_sync = get_latest_job_sync_time(db)
    if latest_job_sync is None:
        raise ValueError("No jobs are available yet")

    existing_matches = get_current_matches_for_user(db, user.id)
    if existing_matches and _matches_are_fresh(existing_matches, latest_resume.uploaded_at, latest_job_sync):
        return existing_matches

    return _recompute_matches(db, user, latest_resume.raw_text)

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.schemas.match import MatchCreate


def get_latest_resume(db: Session, user_id: int) -> Resume | None:
    return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).first()


def get_latest_job_sync_time(db: Session) -> datetime | None:
    return db.query(func.max(Job.fetched_at)).scalar()


def get_jobs_by_ids(db: Session, job_ids: list[int]) -> list[Job]:
    return db.query(Job).filter(Job.id.in_(job_ids)).all()


def get_current_matches_for_user(db: Session, user_id: int) -> list[Match]:
    latest_calculated_at = db.query(func.max(Match.calculated_at)).filter(Match.user_id == user_id).scalar()
    if latest_calculated_at is None:
        return []
    return (
        db.query(Match)
        .filter(Match.user_id == user_id, Match.calculated_at == latest_calculated_at)
        .all()
    )


def create_match(db: Session, match_data: MatchCreate, calculated_at: datetime) -> Match:
    match = Match(
        user_id=match_data.user_id,
        job_id=match_data.job_id,
        score=match_data.score,
        analysis_json=match_data.analysis_json.model_dump(),
        calculated_at=calculated_at,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match

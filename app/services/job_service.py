from sqlalchemy.orm import Session

from app.db.chroma import jobs_collection
from app.models.job import Job
from app.schemas.job import JobCreate
from app.services.embedding_service import embed_text


def get_job_by_external_id(db: Session, external_id: str) -> Job | None:
    return db.query(Job).filter(Job.external_id == external_id).first()


def get_job_by_id(db: Session, job_id: int) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(db: Session, skip: int = 0, limit: int = 20) -> list[Job]:
    return db.query(Job).order_by(Job.fetched_at.desc()).offset(skip).limit(limit).all()


def _index_job_in_chroma(job: Job) -> None:
    embedding_text = f"{job.title} {job.company} {job.description}"
    jobs_collection.add(
        ids=[str(job.id)],
        embeddings=[embed_text(embedding_text)],
        metadatas=[{"title": job.title, "company": job.company}],
    )


def create_job(db: Session, job_data: JobCreate) -> Job:
    job = Job(
        external_id=job_data.external_id,
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        url=str(job_data.url),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    _index_job_in_chroma(job)

    return job

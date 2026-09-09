import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas.job import JobCreate
from app.services.adzuna_client import fetch_jobs
from app.services.job_service import create_job, get_job_by_external_id

logger = logging.getLogger(__name__)


def _map_to_job_create(raw_job: dict) -> JobCreate:
    return JobCreate(
        external_id=raw_job["id"],
        title=raw_job["title"],
        company=raw_job.get("company", {}).get("display_name", "Unknown"),
        description=raw_job["description"],
        url=raw_job["redirect_url"],
    )


def sync_jobs(db: Session) -> dict:
    raw_jobs = fetch_jobs()

    inserted = 0
    skipped_duplicate = 0
    skipped_invalid = 0

    for raw_job in raw_jobs:
        try:
            job_data = _map_to_job_create(raw_job)
        except (KeyError, ValidationError):
            logger.warning("Skipping malformed Adzuna job record: %s", raw_job.get("id", "unknown"))
            skipped_invalid += 1
            continue

        if get_job_by_external_id(db, job_data.external_id) is not None:
            skipped_duplicate += 1
            continue

        create_job(db, job_data)
        inserted += 1

    logger.info(
        "Job sync complete: inserted=%d skipped_duplicate=%d skipped_invalid=%d",
        inserted,
        skipped_duplicate,
        skipped_invalid,
    )
    return {"inserted": inserted, "skipped_duplicate": skipped_duplicate, "skipped_invalid": skipped_invalid}

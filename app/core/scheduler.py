import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import JOB_SYNC_INTERVAL_HOURS
from app.db.session import SessionLocal
from app.services.job_sync_service import sync_jobs

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_job_sync() -> None:
    db = SessionLocal()
    try:
        result = sync_jobs(db)
        logger.info("Scheduled job sync result: %s", result)
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(run_job_sync, "interval", hours=JOB_SYNC_INTERVAL_HOURS, id="job_sync", replace_existing=True)
    scheduler.start()

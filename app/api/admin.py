from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import ADMIN_SYNC_SECRET
from app.db.session import get_db
from app.services.job_sync_service import sync_jobs

router = APIRouter(prefix="/admin", tags=["admin"])


def _verify_admin_secret(x_admin_secret: str = Header(...)) -> None:
    if x_admin_secret != ADMIN_SYNC_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret")


@router.post("/sync-jobs", dependencies=[Depends(_verify_admin_secret)])
def trigger_job_sync(db: Session = Depends(get_db)):
    return sync_jobs(db)

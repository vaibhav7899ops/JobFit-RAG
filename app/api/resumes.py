from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.resume import ResumeCreate, ResumeRead
from app.services.resume_service import create_resume, extract_text_from_upload, get_resumes_by_user

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeRead)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_text = await extract_text_from_upload(file)
    resume_data = ResumeCreate(user_id=current_user.id, raw_text=raw_text)
    return create_resume(db, resume_data)


@router.get("", response_model=list[ResumeRead])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_resumes_by_user(db, current_user.id)

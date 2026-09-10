import io

from docx import Document
from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.schemas.resume import ResumeCreate

MAX_FILE_SIZE_BYTES = 4 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

PDF_MAGIC_BYTES = b"%PDF"
DOCX_MAGIC_BYTES = b"PK\x03\x04"  # .docx is a ZIP archive under the hood


def _has_valid_signature(file_bytes: bytes, extension: str) -> bool:
    if extension == ".pdf":
        return file_bytes.startswith(PDF_MAGIC_BYTES)
    return file_bytes.startswith(DOCX_MAGIC_BYTES)


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


async def extract_text_from_upload(file: UploadFile) -> str:
    filename = file.filename or ""
    extension = filename[filename.rfind(".") :].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds maximum size of 4MB",
        )

    if not _has_valid_signature(file_bytes, extension):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match a valid PDF or DOCX file",
        )

    if extension == ".pdf":
        text = _extract_text_from_pdf(file_bytes)
    else:
        text = _extract_text_from_docx(file_bytes)

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any text from the uploaded file",
        )

    return text


def create_resume(db: Session, resume_data: ResumeCreate) -> Resume:
    resume = Resume(user_id=resume_data.user_id, raw_text=resume_data.raw_text)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resumes_by_user(db: Session, user_id: int) -> list[Resume]:
    return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).all()

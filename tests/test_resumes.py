import io

import pytest
from docx import Document

from app.services.resume_service import _has_valid_signature


def _make_docx_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def _auth_headers(client, email="resumeuser@example.com", password="supersecret") -> dict:
    client.post("/auth/signup", json={"email": email, "password": password})
    token = client.post("/auth/login", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_resume_requires_auth(client):
    docx_bytes = _make_docx_bytes("Some resume text")
    response = client.post(
        "/resumes/upload",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 401


def test_upload_valid_docx_extracts_text(client):
    headers = _auth_headers(client)
    docx_bytes = _make_docx_bytes("Experienced Python developer")
    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Experienced Python developer" in body["raw_text"]


def test_upload_rejects_wrong_extension(client):
    headers = _auth_headers(client, email="badext@example.com")
    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("resume.txt", b"plain text content", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_spoofed_file(client):
    """A .txt file renamed to .pdf with a matching Content-Type header should still be rejected
    by the magic-byte check, not just the (spoofable) extension/content-type check."""
    headers = _auth_headers(client, email="spoofer@example.com")
    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("resume.pdf", b"just plain text, not a real pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_list_resumes_empty_before_upload(client):
    headers = _auth_headers(client, email="noresume@example.com")
    response = client.get("/resumes", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_resumes_after_upload(client):
    headers = _auth_headers(client, email="listresume@example.com")
    docx_bytes = _make_docx_bytes("resume content")
    client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    response = client.get("/resumes", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.parametrize(
    "extension,valid_bytes,invalid_bytes",
    [
        (".pdf", b"%PDF-1.4 rest of file", b"not a pdf at all"),
        (".docx", b"PK\x03\x04 rest of file", b"not a docx at all"),
    ],
)
def test_has_valid_signature(extension, valid_bytes, invalid_bytes):
    assert _has_valid_signature(valid_bytes, extension) is True
    assert _has_valid_signature(invalid_bytes, extension) is False

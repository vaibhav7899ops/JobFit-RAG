from app.schemas.job import JobCreate
from app.services import job_service


def _create_job(db, mocker, external_id: str, title: str = "Software Engineer") -> None:
    mocker.patch.object(job_service, "_index_job_in_chroma")
    job_service.create_job(
        db,
        JobCreate(
            external_id=external_id,
            title=title,
            company="Acme Corp",
            description="Build things.",
            url="https://example.com/jobs/1",
        ),
    )


def test_list_jobs_empty(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_returns_created_jobs(client, db, mocker):
    _create_job(db, mocker, external_id="ext-1")
    _create_job(db, mocker, external_id="ext-2")

    response = client.get("/jobs")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_jobs_pagination_limit(client, db, mocker):
    for i in range(5):
        _create_job(db, mocker, external_id=f"ext-{i}")

    response = client.get("/jobs?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_job_by_id(client, db, mocker):
    _create_job(db, mocker, external_id="ext-single", title="Backend Engineer")

    job_id = db.query(job_service.Job).first().id
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Backend Engineer"


def test_get_nonexistent_job_returns_404(client):
    response = client.get("/jobs/999999")
    assert response.status_code == 404


def test_jobs_endpoint_does_not_require_auth(client, db, mocker):
    _create_job(db, mocker, external_id="ext-public")
    response = client.get("/jobs")
    assert response.status_code == 200

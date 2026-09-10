from app.api import admin
from app.core.config import ADMIN_SYNC_SECRET


def test_sync_jobs_requires_admin_secret(client):
    response = client.post("/admin/sync-jobs")
    assert response.status_code == 422  # missing required header


def test_sync_jobs_rejects_wrong_secret(client):
    response = client.post("/admin/sync-jobs", headers={"X-Admin-Secret": "wrong"})
    assert response.status_code == 401


def test_sync_jobs_triggers_sync_with_correct_secret(client, mocker):
    mock_sync = mocker.patch.object(
        admin, "sync_jobs", return_value={"inserted": 0, "skipped_duplicate": 0, "skipped_invalid": 0}
    )
    response = client.post("/admin/sync-jobs", headers={"X-Admin-Secret": ADMIN_SYNC_SECRET})
    assert response.status_code == 200
    assert response.json() == {"inserted": 0, "skipped_duplicate": 0, "skipped_invalid": 0}
    mock_sync.assert_called_once()

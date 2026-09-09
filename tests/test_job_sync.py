from app.services import job_service, job_sync_service


def _raw_job(job_id: str, url_suffix: str = "abc") -> dict:
    return {
        "id": job_id,
        "title": "Software Engineer",
        "company": {"display_name": "Acme Corp"},
        "description": "Build things.",
        "redirect_url": f"https://www.adzuna.in/land/ad/{job_id}?se={url_suffix}",
    }


def test_sync_inserts_new_jobs(db, mocker):
    mocker.patch.object(job_service, "_index_job_in_chroma")
    mocker.patch.object(job_sync_service, "fetch_jobs", return_value=[_raw_job("111"), _raw_job("222")])

    result = job_sync_service.sync_jobs(db)

    assert result == {"inserted": 2, "skipped_duplicate": 0, "skipped_invalid": 0}


def test_sync_dedupes_by_external_id_even_when_url_changes(db, mocker):
    """Regression test for the real bug found during manual testing: Adzuna's redirect_url
    embeds a per-request tracking token that changes between calls for the SAME job, so
    dedup must key off external_id (Adzuna's stable job id), never the url."""
    mocker.patch.object(job_service, "_index_job_in_chroma")

    mocker.patch.object(job_sync_service, "fetch_jobs", return_value=[_raw_job("111", url_suffix="token-A")])
    job_sync_service.sync_jobs(db)

    mocker.patch.object(job_sync_service, "fetch_jobs", return_value=[_raw_job("111", url_suffix="token-B")])
    result = job_sync_service.sync_jobs(db)

    assert result == {"inserted": 0, "skipped_duplicate": 1, "skipped_invalid": 0}
    assert db.query(job_service.Job).count() == 1


def test_sync_skips_malformed_record_without_aborting_batch(db, mocker):
    mocker.patch.object(job_service, "_index_job_in_chroma")
    good_job = _raw_job("111")
    malformed_job = {"id": "222", "title": "Missing description and company"}

    mocker.patch.object(job_sync_service, "fetch_jobs", return_value=[good_job, malformed_job])
    result = job_sync_service.sync_jobs(db)

    assert result == {"inserted": 1, "skipped_duplicate": 0, "skipped_invalid": 1}

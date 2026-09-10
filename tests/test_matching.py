from datetime import datetime, timedelta, timezone

import pytest

from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.match import BatchAnalysisResponse, JobAnalysisResult, SkillMatch
from app.services import matching_service


def _make_user(db, email="matcher@example.com") -> User:
    user = User(email=email, password_hash="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_resume(db, user_id: int, uploaded_at: datetime) -> Resume:
    resume = Resume(user_id=user_id, raw_text="Python developer resume", uploaded_at=uploaded_at)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def _make_job(db, external_id: str, fetched_at: datetime) -> Job:
    job = Job(
        external_id=external_id,
        title="Software Engineer",
        company="Acme Corp",
        description="Build things.",
        url="https://example.com/job",
        fetched_at=fetched_at,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _mock_retrieval_and_llm(mocker, job_id: int):
    mocker.patch.object(matching_service, "embed_text", return_value=[0.1, 0.2, 0.3])
    mocker.patch.object(
        matching_service.jobs_collection, "query", return_value={"ids": [[str(job_id)]]}
    )
    mocker.patch.object(
        matching_service,
        "analyze_resume_against_jobs",
        return_value=BatchAnalysisResponse(
            analyses=[
                JobAnalysisResult(
                    job_id=job_id,
                    score=75,
                    matching_skills=[SkillMatch(name="Python", reason="Resume mentions Python")],
                    missing_skills=[],
                    summary="Good fit.",
                )
            ]
        ),
    )


def test_no_resume_raises_value_error(db):
    user = _make_user(db)
    with pytest.raises(ValueError, match="Upload a resume"):
        matching_service.get_matches_for_user(db, user)


def test_no_jobs_raises_value_error(db):
    now = datetime.now(timezone.utc)
    user = _make_user(db)
    _make_resume(db, user.id, uploaded_at=now)
    with pytest.raises(ValueError, match="No jobs are available"):
        matching_service.get_matches_for_user(db, user)


def test_empty_candidate_jobs_raises_value_error(db, mocker):
    """Regression test: Chroma returning zero candidates (e.g. jobs exist in Postgres but
    haven't been embedded yet) must not silently send an empty job list to the LLM."""
    now = datetime.now(timezone.utc)
    user = _make_user(db)
    _make_resume(db, user.id, uploaded_at=now)
    _make_job(db, "ext-1", fetched_at=now)

    mocker.patch.object(matching_service, "embed_text", return_value=[0.1, 0.2, 0.3])
    mocker.patch.object(matching_service.jobs_collection, "query", return_value={"ids": [[]]})
    mock_analyze = mocker.patch.object(matching_service, "analyze_resume_against_jobs")

    with pytest.raises(ValueError, match="No matching jobs found"):
        matching_service.get_matches_for_user(db, user)

    mock_analyze.assert_not_called()


def test_recomputes_when_no_existing_matches(db, mocker):
    now = datetime.now(timezone.utc)
    user = _make_user(db)
    _make_resume(db, user.id, uploaded_at=now)
    job = _make_job(db, "ext-1", fetched_at=now)

    _mock_retrieval_and_llm(mocker, job.id)

    matches = matching_service.get_matches_for_user(db, user)

    assert len(matches) == 1
    assert matches[0].score == 75
    matching_service.analyze_resume_against_jobs.assert_called_once()


def test_returns_cached_matches_when_fresh(db, mocker):
    now = datetime.now(timezone.utc)
    user = _make_user(db)
    _make_resume(db, user.id, uploaded_at=now)
    job = _make_job(db, "ext-1", fetched_at=now)

    _mock_retrieval_and_llm(mocker, job.id)
    matching_service.get_matches_for_user(db, user)  # first call: recomputes

    matching_service.analyze_resume_against_jobs.reset_mock()
    second_result = matching_service.get_matches_for_user(db, user)  # second call: should be cached

    matching_service.analyze_resume_against_jobs.assert_not_called()
    assert len(second_result) == 1


def test_recomputes_when_resume_is_newer_than_matches(db, mocker):
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    user = _make_user(db)
    _make_resume(db, user.id, uploaded_at=old_time)
    job = _make_job(db, "ext-1", fetched_at=old_time)

    _mock_retrieval_and_llm(mocker, job.id)
    matching_service.get_matches_for_user(db, user)  # matches calculated_at ~= now, resume/job = old_time

    # Now upload a NEWER resume, making the existing matches stale
    newer_resume_time = datetime.now(timezone.utc) + timedelta(days=1)
    _make_resume(db, user.id, uploaded_at=newer_resume_time)

    matching_service.analyze_resume_against_jobs.reset_mock()
    matching_service.get_matches_for_user(db, user)

    matching_service.analyze_resume_against_jobs.assert_called_once()

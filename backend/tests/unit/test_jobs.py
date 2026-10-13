from datetime import UTC, datetime, timedelta

from linksifty.domain.jobs import Job, JobStatus, claim, release_after_failure

NOW = datetime(2026, 10, 12, tzinfo=UTC)


def test_queued_job_can_be_claimed_once() -> None:
    job = Job.queued("item-1", "user-1", NOW)
    claimed = claim(job, NOW)
    assert claimed.status is JobStatus.PROCESSING
    assert claim(claimed, NOW) is None


def test_expired_lease_can_be_reclaimed() -> None:
    job = Job.queued("item-1", "user-1", NOW)
    claimed = claim(job, NOW)
    assert claimed is not None
    assert claim(claimed, NOW + timedelta(minutes=11)) is not None


def test_second_failure_is_terminal() -> None:
    first_failure = release_after_failure(Job.queued("item-1", "user-1", NOW), transient=True)
    assert first_failure.status is JobStatus.QUEUED
    retried = Job.queued("item-1", "user-1", NOW, attempts=1)
    assert release_after_failure(retried, transient=True).status is JobStatus.FAILED

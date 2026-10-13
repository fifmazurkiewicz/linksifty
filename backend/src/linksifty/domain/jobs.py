"""Pure state transitions for resumable processing jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    AWAITING_MANUAL_CONTENT = "awaiting_manual_content"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Job:
    item_id: str
    user_id: str
    status: JobStatus
    attempts: int
    lease_expires_at: datetime | None

    @classmethod
    def queued(cls, item_id: str, user_id: str, _: datetime, attempts: int = 0) -> Job:
        return cls(item_id, user_id, JobStatus.QUEUED, attempts, None)


def claim(job: Job, now: datetime) -> Job | None:
    """Lease a queued or expired job; active leases remain exclusive."""
    if job.status is JobStatus.QUEUED or (
        job.status is JobStatus.PROCESSING
        and job.lease_expires_at is not None
        and job.lease_expires_at < now
    ):
        return Job(
            job.item_id,
            job.user_id,
            JobStatus.PROCESSING,
            job.attempts + 1,
            now + timedelta(minutes=10),
        )
    return None


def release_after_failure(job: Job, *, transient: bool) -> Job:
    """Allow one retry; expose every final failure instead of silently looping."""
    status = JobStatus.QUEUED if transient and job.attempts < 1 else JobStatus.FAILED
    return Job(job.item_id, job.user_id, status, job.attempts, None)

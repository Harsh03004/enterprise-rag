from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.services.document_processing import process_document
from app.worker import celery_app

MAX_PROCESSING_RETRIES = 3
MAX_PROCESSING_ATTEMPTS = MAX_PROCESSING_RETRIES + 1


def _record_processing_failure(job, document, error: Exception, now: datetime) -> int:
    """Update job/document state and return retries left after this attempt."""
    retries_remaining = max(0, MAX_PROCESSING_ATTEMPTS - job.attempts)
    job.error = str(error)

    if retries_remaining:
        job.status = "retrying"
        job.completed_at = None
        if document is not None:
            # Keep the UI in a processing state during Celery's retry backoff.
            document.status = "processing"
            document.processing_error = None
    else:
        job.status = "failed"
        job.completed_at = now
        if document is not None:
            document.status = "failed"
            document.processing_error = str(error)

    return retries_remaining


@celery_app.task(
    bind=True,
    max_retries=MAX_PROCESSING_RETRIES,
    autoretry_for=(),
    name="documents.process",
)
def process_document_task(self, document_id: int, job_id: int) -> int:
    db = SessionLocal()
    job = None

    try:
        job = db.get(ProcessingJob, job_id)
        document = db.get(Document, document_id)

        if job is None or document is None:
            return 0

        job.status = "processing"
        job.attempts += 1
        job.started_at = datetime.now(UTC)
        job.error = None
        document.status = "processing"
        document.processing_error = None
        db.commit()

        chunk_count = process_document(
            db=db,
            document=document,
            rebuild_chunks=job.rebuild_chunks,
        )

        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        db.commit()

        return chunk_count

    except Exception as exc:
        db.rollback()

        retries_remaining = 0
        if job is not None:
            job = db.get(ProcessingJob, job_id)
            if job is not None:
                document = db.get(Document, document_id)
                retries_remaining = _record_processing_failure(
                    job=job,
                    document=document,
                    error=exc,
                    now=datetime.now(UTC),
                )
                db.commit()

        if retries_remaining:
            raise self.retry(
                exc=exc,
                countdown=2 ** min(job.attempts, 6),
                max_retries=self.request.retries + retries_remaining,
            ) from exc

        raise

    finally:
        db.close()


@celery_app.task(name="documents.recover_stale")
def recover_stale_document_jobs() -> int:
    """Requeue tasks abandoned by a worker crash and terminally fail exhausted jobs."""
    now = datetime.now(UTC)
    db = SessionLocal()
    scheduled: list[tuple[int, int]] = []
    try:
        candidates = db.scalars(
            select(ProcessingJob)
            .where(
                or_(
                    (ProcessingJob.status == "queued") & (ProcessingJob.created_at < now - timedelta(minutes=2)),
                    (ProcessingJob.status == "retrying") & (ProcessingJob.started_at < now - timedelta(minutes=2)),
                    (ProcessingJob.status == "processing") & (ProcessingJob.started_at < now - timedelta(minutes=15)),
                )
            )
            .with_for_update(skip_locked=True)
        ).all()
        for job in candidates:
            document = db.get(Document, job.document_id)
            if document is None:
                job.status = "failed"
                job.error = "Document was removed while processing."
                job.completed_at = now
            elif job.attempts < MAX_PROCESSING_ATTEMPTS:
                job.status = "retrying"
                job.error = "Recovered an interrupted document processing attempt."
                job.started_at = now
                document.status = "processing"
                document.processing_error = None
                scheduled.append((document.id, job.id))
            else:
                job.status = "failed"
                job.error = "Document processing stopped after repeated worker interruptions."
                job.completed_at = now
                document.status = "failed"
                document.processing_error = job.error
        db.commit()
        for document_id, job_id in scheduled:
            process_document_task.apply_async(args=(document_id, job_id))
        return len(scheduled)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.services.document_processing import process_document
from app.worker import celery_app


@celery_app.task(
    bind=True,
    max_retries=3,
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

        chunk_count = process_document(db=db, document=document)

        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        db.commit()

        return chunk_count

    except Exception as exc:
        db.rollback()

        if job is not None:
            job = db.get(ProcessingJob, job_id)
            if job is not None:
                job.error = str(exc)
                job.status = (
                    "retrying" if self.request.retries < self.max_retries else "failed"
                )
                db.commit()

        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc, countdown=2 ** (self.request.retries + 1)
            ) from exc

        raise

    finally:
        db.close()

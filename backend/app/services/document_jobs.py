from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.tasks import process_document_task


def enqueue_document_processing(
    db: Session,
    document: Document,
) -> ProcessingJob:
    job = ProcessingJob(
        document_id=document.id,
        status="queued",
    )
    document.status = "processing"
    document.processing_error = None

    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        process_document_task.delay(document.id, job.id)
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        document.status = "failed"
        document.processing_error = "Document processing could not be queued."
        db.commit()
        raise RuntimeError("Document processing could not be queued.") from exc

    return job

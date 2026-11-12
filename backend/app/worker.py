from celery import Celery
from celery.signals import setup_logging, task_postrun, task_prerun

from app.core.config import settings
from app.core.logging import configure_logging, request_id_var

celery_app = Celery(
    "enterprise_rag",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "recover-stale-document-jobs-every-minute": {
            "task": "documents.recover_stale",
            "schedule": 60.0,
        }
    },
)

celery_app.autodiscover_tasks(["app"])


@setup_logging.connect
def _configure_worker_logging(**_kwargs) -> None:
    # Replace Celery's own logging setup with the shared JSON/text format.
    configure_logging(settings.log_level, settings.log_format)


@task_prerun.connect
def _bind_task_id(task_id=None, **_kwargs) -> None:
    request_id_var.set(task_id)


@task_postrun.connect
def _unbind_task_id(**_kwargs) -> None:
    request_id_var.set(None)

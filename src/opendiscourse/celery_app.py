"""Celery application for background ingestion tasks."""

from celery import Celery
from opendiscourse.config import get_settings

settings = get_settings()

celery_app = Celery(
    "opendiscourse",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "sync-congress-daily": {
            "task": "opendiscourse.ingestion.congress_gov.sync_daily",
            "schedule": 86400.0,
        },
        "sync-fec-quarterly": {
            "task": "opendiscourse.ingestion.fec.sync_quarterly",
            "schedule": 7776000.0,
        },
    },
)

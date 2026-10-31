from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_instance = Celery(
    "tasks",
    broker=settings.CASH_URL,
    include=[
        "src.tasks.tasks",
    ],
)

celery_instance.conf.timezone = 'Europe/Moscow'
celery_instance.conf.enable_utc = False

celery_instance.conf.beat_schedule = {
    "refresh-events": {
        "task": "delete_past_events",
        "schedule": crontab(minute=00, hour=00),  # каждый день в 00:00
    }
}
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "siteconv.settings")
app = Celery("siteconv")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-temp-files": {
        "task": "converter.tasks.cleanup_temp_folder",
        "schedule": crontab(minute=f"*/{settings.FILE_TTL // 60}"),
    },
}

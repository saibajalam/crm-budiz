import os
import sys
from pathlib import Path
from celery import Celery

# Ensure Django apps inside `budiz_platform/` are importable when running Celery CLI.
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir / "budiz_platform"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

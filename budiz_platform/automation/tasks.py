from celery import shared_task

from .engine import process_event
from workspaces.models import Workspace


@shared_task(bind=True, max_retries=3)
def run_automation_event(self, workspace_id, event_name, payload, user_id=None):
    """
    Async wrapper around automation engine.
    """

    try:
        workspace = Workspace.objects.filter(id=workspace_id).first()
        if not workspace:
            return

        process_event(
            event_name=event_name,
            payload=payload,
            workspace=workspace,
            user=None,  # optional: fetch user if needed
        )

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)

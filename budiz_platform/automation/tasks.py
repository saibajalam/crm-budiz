from celery import shared_task


@shared_task(bind=True, max_retries=3)
def process_automation_event(self, workspace_id, event_name, payload):
    from .engine import run_engine as run_automation_engine

    run_automation_engine(
        workspace_id=workspace_id,
        event_name=event_name,
        payload=payload,
    )

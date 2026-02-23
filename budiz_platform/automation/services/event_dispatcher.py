import logging
from django.conf import settings

from ..tasks import run_automation_event

logger = logging.getLogger(__name__)


def emit_event(
    *,
    event_name: str,
    workspace,
    payload: dict,
    user=None,
    allow_sync_fallback: bool = True,
):
    """
    CENTRAL AUTOMATION EVENT DISPATCHER

    - Requires explicit payload.
    - Requires workspace.
    - Async dispatch via Celery.
    """

    if not isinstance(payload, dict):
        raise ValueError("Event payload must be a dictionary.")

    if not event_name:
        raise ValueError("Event name must be provided.")

    if not workspace:
        return  # Cannot process without workspace context

    try:
        run_automation_event.apply_async(
            kwargs={
                "workspace_id": workspace.id,
                "event_name": event_name,
                "payload": payload,
                "user_id": user.id if user else None,
            },
            retry=False,
            ignore_result=True,
        )
        return
    except Exception:
        logger.exception(
            "Celery dispatch failed for automation event; falling back to sync execution"
        )

    if not allow_sync_fallback:
        return

    if not getattr(settings, "AUTOMATION_SYNC_FALLBACK", True):
        return

    try:
        from ..engine import process_event

        process_event(
            event_name=event_name,
            payload=payload,
            workspace=workspace,
            user=user,
        )
    except Exception:
        logger.exception("Synchronous fallback failed for automation event dispatch")

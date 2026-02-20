from ..tasks import run_automation_event


def emit_event(event_name, instance, user=None):
    workspace = getattr(instance, "workspace", None)
    payload = {
        "target_object_id": instance.id,
        "target_model": instance.__class__.__name__,
        "workspace_id": workspace.id,
        "user_id": user.id if user else None,
    }
    if user:
        payload["user_id"] = user.id

    if not workspace:
        return

    # async dispatch to Celery
    run_automation_event.delay(
        workspace_id=workspace.id,
        event_name=event_name,
        payload=payload,
        user_id=user.id if user else None,
    )

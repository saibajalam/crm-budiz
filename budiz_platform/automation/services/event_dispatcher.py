from ..engine import process_event


def emit_event(event_name, instance, user=None):
    workspace = getattr(instance, "workspace", None)
    payload = {
        "object_id": instance.id,
        "model": instance.__class__.__name__,
        "workspace_id": workspace.id,
        "user_id": user.id if user else None,
    }
    if user:
        payload["user_id"] = user.id

    if not workspace:
        return

    # Direct call to engine (sync)
    process_event(event_name, payload, workspace, user)

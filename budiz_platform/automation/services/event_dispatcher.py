from ..engine import process_event


def emit_event(event_name, instance, user=None):
    workspace = getattr(instance, "workspace", None)
    payload = {
        "id": instance.id,
        "model": instance.__class__.__name__,
    }
    if user:
        payload["user_id"] = user.id

    # Direct call to engine (sync)
    process_event(event_name, payload, workspace, user)

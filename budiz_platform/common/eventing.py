def emit_crm_event(*, event_name, workspace, payload, user=None):
    """Best-effort event emission for automation/real-time consumers."""
    try:
        from automation.services.event_dispatcher import emit_event

        emit_event(
            event_name=event_name,
            workspace=workspace,
            payload=payload,
            user=user,
        )
    except Exception:
        # Non-blocking by design.
        return

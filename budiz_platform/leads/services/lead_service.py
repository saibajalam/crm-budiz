from django.db import transaction
from leads.models import Lead


@transaction.atomic
def create_lead(*, workspace, payload: dict, created_by, automation_sync_fallback=True):
    """
    CENTRAL LEAD CREATION SERVICE
    All lead creation must go through here.
    Triggers automation events.
    """

    payload = dict(payload)
    payload.pop("workspace", None)
    payload.pop("created_by", None)

    lead = Lead.objects.create(
        workspace=workspace,
        created_by=created_by,
        **payload,
    )

    # ---------------------------------------
    # AUTOMATION EVENT
    # ---------------------------------------
    _emit_lead_created_event(
        lead,
        created_by,
        allow_sync_fallback=automation_sync_fallback,
    )

    return lead


# ---------------------------------------
# EVENT EMITTER
# ---------------------------------------
def _emit_lead_created_event(lead, user, allow_sync_fallback=True):
    """
    Emits 'lead.created' automation event.
    Lazy import to avoid circular imports.
    """

    try:
        from automation.services.event_dispatcher import emit_event
    except Exception:
        return

    emit_event(
        event_name="lead.created",
        workspace=lead.workspace,
        payload={
            "target_object_id": lead.id,
            "target_model": "Lead",
            "email": lead.email,
            "phone": lead.phone,
            "status": lead.status,
            "assigned_to": getattr(lead, "assigned_to_id", None),
        },
        user=user,
        allow_sync_fallback=allow_sync_fallback,
    )

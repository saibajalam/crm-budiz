from django.db import transaction
from leads.models import Lead


@transaction.atomic
def create_lead(*, workspace, payload: dict, created_by):
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
    _emit_lead_created_event(lead, created_by)

    return lead


# ---------------------------------------
# EVENT EMITTER
# ---------------------------------------
def _emit_lead_created_event(lead, user):
    """
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
            "id": lead.id,
            "model": "lead",
            "email": lead.email,
            "phone": lead.phone,
            "status": lead.status,
            "assigned_to": lead.assigned_to_id,
        },
        user=user,
    )

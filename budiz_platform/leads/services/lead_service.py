from django.db import transaction
from leads.models import Lead

# automation import
try:
    from automation.services.event_dispatcher import emit_event
except Exception:
    emit_event = None


@transaction.atomic
def create_lead(*, workspace, payload: dict, created_by):
    """
    Central place for creating leads.
    ALL lead creation must go through here.
    """

    payload = dict(payload)
    payload.pop("workspace", None)
    payload.pop("created_by", None)

    lead = Lead.objects.create(workspace=workspace, created_by=created_by, **payload)

    # 🔥 AUTOMATION TRIGGER
    if emit_event:
        emit_event(
            event_name="lead_created",
            instance=lead,
            user=created_by,
        )

    return lead

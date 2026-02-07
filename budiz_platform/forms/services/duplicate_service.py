from django.db.models import Q
from leads.models import Lead


def get_or_create_lead(form, payload):
    workspace = form.workspace

    email = payload.get("email")
    phone = payload.get("phone")

    lead = None

    if form.duplicate_handling == "update":
        lead = Lead.objects.filter(workspace=workspace, email=email).first()

    elif form.duplicate_handling == "configurable":
        lead = (
            Lead.objects.filter(workspace=workspace)
            .filter(Q(email=email) | Q(phone=phone))
            .first()
        )

    if not lead:
        lead = Lead.objects.create(workspace=workspace, **payload)
    else:
        for k, v in payload.items():
            setattr(lead, k, v)
        lead.save()

    return lead

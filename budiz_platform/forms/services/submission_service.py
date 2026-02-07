from django.db import transaction
from django.db.models import Q

from ..models import FormSubmission
from .duplicate_service import get_or_create_lead
from .assignment_service import assign_lead_from_form
from .response_service import create_responses


@transaction.atomic
def submit_public_form(*, form, data: dict):
    workspace = form.workspace

    lead_payload = {}
    answers = []

    for field in form.fields.all():
        if field.label in data:
            value = data[field.label]

            answers.append(
                {
                    "field_id": field.id,
                    "value": value,
                }
            )

            if field.map_to_lead_field != "none":
                lead_payload[field.map_to_lead_field] = value

    # 🔥 DUPLICATE SERVICE
    lead = get_or_create_lead(form, lead_payload)

    # 🔥 ASSIGNMENT SERVICE
    assign_lead_from_form(form=form, lead=lead)

    # 🔥 CREATE SUBMISSION
    submission = FormSubmission.objects.create(
        form=form,
        workspace=workspace,
        lead=lead,
    )

    # 🔥 CREATE RESPONSES
    create_responses(
        submission=submission,
        answers=answers,
        created_by=None,
    )

    return submission

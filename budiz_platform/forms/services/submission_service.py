from django.db import transaction
from django.db.models import Q

from ..models import FormSubmission
from .duplicate_service import get_or_create_lead
from .assignment_service import assign_lead_from_form
from .response_service import create_responses
from leads.services.lead_service import create_lead
from common.counter import get_next_display_number


@transaction.atomic
def submit_public_form(*, form, data: dict):
    workspace = form.workspace

    def looks_like_email(value):
        return isinstance(value, str) and "@" in value and "." in value

    def normalize_label(label):
        return " ".join(label.lower().split())

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

            map_field = field.map_to_lead_field

            if map_field == "none":
                normalized_label = normalize_label(field.label)
                if "first name" in normalized_label:
                    map_field = "first_name"
                elif "last name" in normalized_label:
                    map_field = "last_name"
                elif "full name" in normalized_label:
                    if isinstance(value, str):
                        parts = value.strip().split()
                        if parts:
                            lead_payload.setdefault("first_name", parts[0])
                            if len(parts) > 1:
                                lead_payload.setdefault(
                                    "last_name", " ".join(parts[1:])
                                )
                    continue
                elif "email" in normalized_label:
                    map_field = "email"
                elif "phone" in normalized_label:
                    map_field = "phone"

            if map_field in {"first_name", "last_name"} and looks_like_email(value):
                map_field = "email"

            if map_field != "none":
                lead_payload[map_field] = value

    lead_payload["display_number"] = get_next_display_number(workspace, "lead")

    # DUPLICATE SERVICE
    lead = create_lead(
        workspace=workspace,
        payload=lead_payload,
        created_by=form.created_by,
    )

    # ASSIGNMENT SERVICE
    assign_lead_from_form(form=form, lead=lead)

    # CREATE SUBMISSION
    submission = FormSubmission.objects.create(
        form=form,
        workspace=workspace,
        lead=lead,
    )

    # RESPONSE SERVICE
    create_responses(
        submission=submission,
        answers=answers,
        created_by=form.created_by,
    )

    return submission

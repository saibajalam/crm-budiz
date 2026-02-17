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
        return " ".join(str(label).lower().replace("_", " ").split())

    normalized_data = {
        normalize_label(key): value for key, value in (data or {}).items()
    }

    def split_full_name(value):
        if not isinstance(value, str):
            return None, None
        parts = value.strip().split()
        if not parts:
            return None, None
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        return first_name, last_name

    full_name_first, full_name_last = split_full_name(normalized_data.get("full name"))

    lead_payload = {}
    answers = []

    for field in form.fields.all():
        field_key = normalize_label(field.label)
        value = None
        if field_key in normalized_data:
            value = normalized_data[field_key]
        elif field_key == "first name" and full_name_first:
            value = full_name_first
        elif field_key == "last name" and full_name_last:
            value = full_name_last

        if value is not None:

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

    if "email" in normalized_data and "email" not in lead_payload:
        lead_payload["email"] = normalized_data["email"]

    if "phone" in normalized_data and "phone" not in lead_payload:
        lead_payload["phone"] = normalized_data["phone"]

    if "full name" in normalized_data:
        full_name = normalized_data["full name"]
        if isinstance(full_name, str):
            name_parts = full_name.strip().split()
            if name_parts and "first_name" not in lead_payload:
                lead_payload["first_name"] = name_parts[0]
            if len(name_parts) > 1 and "last_name" not in lead_payload:
                lead_payload["last_name"] = " ".join(name_parts[1:])

    if "company_name" in normalized_data and "company" not in lead_payload:
        lead_payload["company"] = normalized_data["company_name"]

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

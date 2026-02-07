from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from forms.models import FormResponse, FormField


@transaction.atomic
def create_responses(*, submission, answers: list, created_by=None, strict=True):
    if not answers:
        return []

    field_ids = [a["field_id"] for a in answers]

    fields = FormField.objects.filter(id__in=field_ids, form=submission.form)

    field_map = {f.id: f for f in fields}

    now = timezone.now()
    responses = []

    for ans in answers:
        field_id = ans.get("field_id")
        value = ans.get("value")

        field = field_map.get(field_id)

        if not field:
            if strict:
                raise ValidationError(f"Invalid field_id {field_id}")
            continue

        responses.append(
            FormResponse(
                submission=submission,
                field=field,
                value=value,
                workspace=submission.workspace,
                created_by=created_by,
                created_at=now,
            )
        )

    created = FormResponse.objects.bulk_create(responses)
    return created

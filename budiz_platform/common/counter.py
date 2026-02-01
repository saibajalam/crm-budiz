from django.db import transaction
from .models import WorkspaceCounter

def get_next_display_number(workspace, entity):
    with transaction.atomic():
        counter, _ = WorkspaceCounter.objects.select_for_update().get_or_create(
            workspace=workspace,
            entity=entity,
            defaults={"current_value": 0},
        )

        counter.current_value += 1
        counter.save(update_fields=["current_value"])

        return counter.current_value

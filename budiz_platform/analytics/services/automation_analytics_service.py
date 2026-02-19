from datetime import date
from django.db import transaction
from ..models import AutomationAnalytics


@transaction.atomic
def update_automation_metrics(workspace, success=True):
    today = date.today()

    obj, _ = AutomationAnalytics.objects.get_or_create(
        workspace=workspace,
        date=today,
    )

    obj.total_executions += 1

    if success:
        obj.success_count += 1
    else:
        obj.failed_count += 1

    obj.save(
        update_fields=[
            "total_executions",
            "success_count",
            "failed_count",
        ]
    )

    return obj

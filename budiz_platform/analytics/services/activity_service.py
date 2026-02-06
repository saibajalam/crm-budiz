from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from leads.models import LeadActivity


def get_activity_stats(workspace, days=30):
    now = timezone.now()
    start_date = now - timedelta(days=days)

    qs = LeadActivity.objects.filter(
        workspace=workspace,
        is_deleted=False,
    ).select_related(
        "lead",
        "lead__assigned_to",
        "user",
    )

    total = qs.count()

    completed = qs.filter(is_completed=True, completed_at__gte=start_date).count()

    upcoming = qs.filter(is_completed=False, due_date__gte=now).count()

    overdue = qs.filter(is_completed=False, due_date__lt=now).count()

    return {
        "total": total,
        "completed": completed,
        "upcoming": upcoming,
        "overdue": overdue,
    }

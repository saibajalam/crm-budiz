from deals.models import DealActivity
from django.utils import timezone


def get_workspace_deal_activity_queryset(
    *,
    workspace,
    deal_id=None,
    activity_type=None,
    user_id=None,
    start_date=None,
    end_date=None,
    category=None,
):
    queryset = DealActivity.objects.filter(workspace=workspace, is_deleted=False)

    if deal_id:
        queryset = queryset.filter(deal_id=deal_id)

    if activity_type:
        queryset = queryset.filter(activity_type__iexact=activity_type)

    if user_id:
        queryset = queryset.filter(assigned_to_id=user_id)

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    if category == "upcoming":
        queryset = queryset.filter(
            due_date__gt=timezone.now(), status__in=["pending", "cancelled"]
        )
    elif category == "overdue":
        queryset = queryset.filter(
            due_date__lt=timezone.now(), status__in=["pending", "cancelled"]
        )
    elif category == "completed":
        queryset = queryset.filter(status="completed")

    return queryset

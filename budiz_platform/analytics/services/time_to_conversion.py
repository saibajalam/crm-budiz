from django.db.models import F, Avg, Count, DurationField, ExpressionWrapper
from deals.models import Deal


def time_to_conversion_analytics(workspace, days=30):
    qs = Deal.objects.filter(
        workspace=workspace,
        pipeline_stage="closed_won",
        won_at__isnull=False,
        created_from_lead__isnull=False,
    ).select_related(
        "assigned_to",
        "created_from_lead",
        "created_from_lead__form",
    )

    qs = qs.annotate(
        conversion_time=ExpressionWrapper(
            F("won_at") - F("created_from_lead__created_at"),
            output_field=DurationField(),
        )
    )

    # WORKSPACE SUMMARY
    workspace_summary = qs.aggregate(
        total_conversions=Count("id"),
        avg_conversion_time=Avg("conversion_time"),
    )

    # PER USER
    per_user = (
        qs.values("assigned_to", "assigned_to__full_name")
        .annotate(
            total_conversions=Count("id"),
            avg_conversion_time=Avg("conversion_time"),
        )
        .order_by("-total_conversions")
    )

    # PER FORM
    # (assuming lead has form FK)
    per_form = (
        qs.values(
            "created_from_lead__form",
            "created_from_lead__form__name",
        )
        .annotate(
            total_conversions=Count("id"),
            avg_conversion_time=Avg("conversion_time"),
        )
        .order_by("-total_conversions")
    )

    return {
        "workspace_summary": workspace_summary,
        "per_user": list(per_user),
        "per_form": list(per_form),
    }

from django.db.models import (
    Sum,
    Count,
    Avg,
    Q,
    F,
    ExpressionWrapper,
    DecimalField,
    DurationField,
)
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from deals.models import Deal


def get_revenue_dashboard(workspace, days=30):
    now = timezone.now()
    start_date = now - timedelta(days=days)

    base_qs = Deal.objects.filter(
        workspace=workspace,
        is_deleted=False,
    ).select_related(
        "assigned_to",
        "created_from_lead",
    )

    won_qs = base_qs.filter(
        pipeline_stage="closed_won",
        won_at__isnull=False,
    )

    open_qs = base_qs.exclude(pipeline_stage__in=["closed_won", "closed_lost"])

    # ===============================
    # TOTAL REVENUE
    # ===============================
    total_revenue = won_qs.aggregate(total=Sum("value"))["total"] or 0

    # ===============================
    # PERIOD REVENUE
    # ===============================
    period_revenue = (
        won_qs.filter(won_at__gte=start_date).aggregate(total=Sum("value"))["total"]
        or 0
    )

    # ===============================
    # PIPELINE VALUE
    # ===============================
    pipeline_value = open_qs.aggregate(total=Sum("value"))["total"] or 0

    # ===============================
    # FORECAST VALUE
    # ===============================
    forecast_value = (
        open_qs.annotate(
            weighted=ExpressionWrapper(
                F("value") * F("probability") / 100,
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        ).aggregate(total=Sum("weighted"))["total"]
        or 0
    )

    # ===============================
    # AVG DEAL SIZE
    # ===============================
    avg_deal_size = won_qs.aggregate(avg=Avg("value"))["avg"] or 0

    # ===============================
    # WIN RATE
    # ===============================
    total_deals = base_qs.count()
    total_won = won_qs.count()

    win_rate = (total_won / total_deals * 100) if total_deals else 0

    # ===============================
    # FORECAST VS ACTUAL
    # ===============================
    forecast_vs_actual = {
        "forecast": forecast_value,
        "actual": total_revenue,
        "accuracy_percent": (
            (total_revenue / forecast_value * 100) if forecast_value else 0
        ),
    }

    # ===============================
    # MONTHLY REVENUE (won_at)
    # ===============================
    monthly_revenue = (
        won_qs.annotate(month=TruncMonth("won_at"))
        .values("month")
        .annotate(total=Sum("value"))
        .order_by("month")
    )

    # ===============================
    # BEST MONTH
    # ===============================
    best_month = (
        won_qs.annotate(month=TruncMonth("won_at"))
        .values("month")
        .annotate(total=Sum("value"))
        .order_by("-total")
        .first()
    )

    # ===============================
    # REVENUE BY USER
    # ===============================
    revenue_by_user = (
        won_qs.values("assigned_to", "assigned_to__full_name")
        .annotate(
            revenue=Sum("value"),
            deals_won=Count("id"),
            avg_deal=Avg("value"),
        )
        .order_by("-revenue")
    )

    # ===============================
    # REVENUE BY FORM
    # ===============================
    revenue_by_form = (
        won_qs.filter(created_from_lead__formsubmission__form__isnull=False)
        .values(
            "created_from_lead__formsubmission__form",
            "created_from_lead__formsubmission__form__name",
        )
        .annotate(
            revenue=Sum("value"),
            deals_won=Count("id"),
        )
        .order_by("-revenue")
    )

    # ===============================
    # SALES VELOCITY
    # avg time lead → won
    # ===============================
    velocity_qs = won_qs.filter(created_from_lead__isnull=False).annotate(
        duration=ExpressionWrapper(
            F("won_at") - F("created_from_lead__created_at"),
            output_field=DurationField(),
        )
    )

    sales_velocity = velocity_qs.aggregate(avg=Avg("duration"))["avg"]

    return {
        "summary": {
            "total_revenue": total_revenue,
            "period_revenue": period_revenue,
            "pipeline_value": pipeline_value,
            "forecast_value": forecast_value,
            "avg_deal_size": avg_deal_size,
            "win_rate": round(win_rate, 2),
        },
        "forecast_vs_actual": forecast_vs_actual,
        "monthly_revenue": list(monthly_revenue),
        "best_month": best_month,
        "revenue_by_user": list(revenue_by_user),
        "revenue_by_form": list(revenue_by_form),
        "sales_velocity": sales_velocity,
    }

from django.db.models import Count, Q
from leads.models import Lead
from deals.models import Deal


# USER FUNNEL
def get_user_funnel(workspace):
    qs = Deal.objects.filter(
        workspace=workspace,
        is_deleted=False,
        assigned_to__isnull=False,
    )

    data = (
        qs.values("assigned_to", "assigned_to__full_name")
        .annotate(
            deals_assigned=Count("id"),
            deals_won=Count("id", filter=Q(pipeline_stage="closed_won")),
        )
        .order_by("-deals_won")
    )

    results = []

    for row in data:
        assigned = row["deals_assigned"]
        won = row["deals_won"]

        win_rate = (won / assigned * 100) if assigned else 0

        results.append(
            {
                "user_id": row["assigned_to"],
                "user_name": row["assigned_to__full_name"],
                "deals_assigned": assigned,
                "deals_won": won,
                "win_rate": round(win_rate, 2),
            }
        )

    return results

from analytics.services.funnel_service import get_user_funnel
from analytics.services.revenue_service import get_revenue_dashboard
from analytics.services.time_to_conversion import time_to_conversion_analytics
from analytics.services.activity_service import get_activity_stats
from django.db.models import (
    F,
    Count,
    Sum,
    Avg,
    ExpressionWrapper,
    DecimalField,
    DurationField,
)
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from deals.models import Deal
from leads.models import LeadActivity


CACHE_TTL = 300  # seconds, 5 min


def get_dashboard_data(workspace, days=30):
    """
    Returns a fully optimized and cached unified analytics dashboard.
    """
    cache_key = f"dashboard_workspace_{workspace.id}_days_{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    user_funnel = get_user_funnel(workspace)
    revenue = get_revenue_dashboard(workspace, days)
    conversion = time_to_conversion_analytics(workspace, days)
    activities = get_activity_stats(workspace, days)

    result = {
        "revenue": revenue,
        "user_performance": user_funnel,
        "conversion_time": conversion,
        "activities": activities,
    }

    cache.set(cache_key, result, CACHE_TTL)
    return result

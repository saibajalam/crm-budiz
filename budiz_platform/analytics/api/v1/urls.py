from django.urls import path
from .views import (
    AnalyticsDashboardAPIView,
    DealAnalyticsListAPIView,
    UserAnalyticsListAPIView,
    UserAnalyticsDetailAPIView,
    AnalyticsTrendsAPIView,
)

app_name = "analytics"

urlpatterns = [
    # Dashboard/Summary
    path(
        "analytics/dashboard/",
        AnalyticsDashboardAPIView.as_view(),
        name="analytics_dashboard",
    ),
    # Deal Analytics
    path(
        "analytics/deals/",
        DealAnalyticsListAPIView.as_view(),
        name="deal_analytics_list",
    ),
    # User Analytics
    path(
        "analytics/users/",
        UserAnalyticsListAPIView.as_view(),
        name="user_analytics_list",
    ),
    path(
        "analytics/users/<int:pk>/",
        UserAnalyticsDetailAPIView.as_view(),
        name="user_analytics_detail",
    ),
    # Trends and Charts
    path(
        "analytics/trends/", AnalyticsTrendsAPIView.as_view(), name="analytics_trends"
    ),
]

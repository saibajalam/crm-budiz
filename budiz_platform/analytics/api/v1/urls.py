from django.urls import path
from .views import (
    AnalyticsDashboardAPIView,
    AutomationRulePerformanceAPIView,
    DealAnalyticsListAPIView,
    UserAnalyticsListAPIView,
    UserAnalyticsDetailAPIView,
    AnalyticsTrendsAPIView,
    FormConversionFunnelAPIView,
    WorkspaceFunnelDashboardAPIView,
    TimeToConversionAPIView,
    FormTrendAPIView,
    UserConversionFunnelAPIView,
    RevenueDashboardAPIView,
    UnifiedDashboardAPIView,
    AutomationDashboardAPIView,
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
        "analytics/users/<int:user_id>/",
        UserAnalyticsDetailAPIView.as_view(),
        name="user_analytics_detail",
    ),
    path(
        "analytics/trends/", AnalyticsTrendsAPIView.as_view(), name="analytics_trends"
    ),
    path(
        "forms/<int:form_id>/conversion-funnel/",
        FormConversionFunnelAPIView.as_view(),
        name="form-conversion-funnel",
    ),
    path(
        "workspace/users/conversion-funnel/",
        UserConversionFunnelAPIView.as_view(),
        name="user-conversion-funnel",
    ),
    path(
        "workspace/funnel-dashboard/",
        WorkspaceFunnelDashboardAPIView.as_view(),
        name="workspace-funnel-dashboard",
    ),
    path(
        "workspace/time-to-conversion/",
        TimeToConversionAPIView.as_view(),
        name="time-to-conversion",
    ),
    path("forms/<int:form_id>/trend/", FormTrendAPIView.as_view(), name="form-trend"),
    path(
        "workspace/revenue-dashboard/",
        RevenueDashboardAPIView.as_view(),
        name="revenue-dashboard",
    ),
    path(
        "workspace/unified-dashboard/",
        UnifiedDashboardAPIView.as_view(),
        name="unified-dashboard",
    ),
    path(
        "automation/dashboard/",
        AutomationDashboardAPIView.as_view(),
        name="automation-dashboard",
    ),
    path(
        "automation/rules/",
        AutomationRulePerformanceAPIView.as_view(),
        name="automation-rules",
    ),
]

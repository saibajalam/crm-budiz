from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from ...models import DealAnalytics, UserAnalytics
from .serializers import (
    DealAnalyticsSerializer,
    UserAnalyticsSerializer,
    AnalyticsSummarySerializer,
)
from subscriptions.permissions import HasActiveSubscription
from workspaces.utils import get_user_workspace
from workspaces.permissions import IsWorkspaceMember


class AnalyticsDashboardAPIView(APIView):
    """
    Dashboard view providing summary analytics for the user's workspace
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {"error": "No active workspace found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get date range (default to last 30 days)
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Current period analytics
        current_deal_stats = DealAnalytics.objects.filter(
            workspace=workspace, date__range=[start_date, end_date]
        ).aggregate(
            total_deals=Sum("total_deals"),
            total_pipeline_value=Sum("pipeline_value"),
            won_deals=Sum("won_deals"),
            won_value=Sum("won_value"),
            lost_deals=Sum("lost_deals"),
            leads_converted=Sum("leads_converted"),
            total_qualified_leads=Sum("total_leads_qualified"),
        )

        current_user_stats = UserAnalytics.objects.filter(
            workspace=workspace, date__range=[start_date, end_date]
        ).aggregate(
            active_users=Count("user", distinct=True),
            total_activities=Sum("activities_completed"),
            total_deals_created=Sum("deals_created"),
            total_revenue=Sum("revenue_generated"),
        )

        # Previous period for comparison
        prev_start_date = start_date - timedelta(days=days)
        prev_end_date = start_date

        prev_deal_stats = DealAnalytics.objects.filter(
            workspace=workspace, date__range=[prev_start_date, prev_end_date]
        ).aggregate(
            prev_won_value=Sum("won_value"), prev_total_deals=Sum("total_deals")
        )

        # Calculate metrics
        total_deals = current_deal_stats.get("total_deals") or 0
        won_deals = current_deal_stats.get("won_deals") or 0
        won_value = current_deal_stats.get("won_value") or 0
        prev_won_value = prev_deal_stats.get("prev_won_value") or 0
        leads_converted = current_deal_stats.get("leads_converted") or 0
        total_qualified_leads = current_deal_stats.get("total_qualified_leads") or 0

        win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
        conversion_rate = (
            (leads_converted / total_qualified_leads * 100)
            if total_qualified_leads > 0
            else 0
        )

        # Growth calculations
        revenue_growth = (
            ((won_value - prev_won_value) / prev_won_value * 100)
            if prev_won_value > 0
            else 0
        )

        active_users = current_user_stats.get("active_users") or 0
        total_deals_created = current_user_stats.get("total_deals_created") or 0
        avg_deals_per_user = (
            (total_deals_created / active_users) if active_users > 0 else 0
        )

        summary_data = {
            "total_deals": total_deals,
            "total_pipeline_value": current_deal_stats.get("total_pipeline_value") or 0,
            "won_deals": won_deals,
            "won_value": won_value,
            "lost_deals": current_deal_stats.get("lost_deals") or 0,
            "win_rate": round(win_rate, 2),
            "leads_converted": leads_converted,
            "conversion_rate": round(conversion_rate, 2),
            "total_qualified_leads": total_qualified_leads,
            "active_users": active_users,
            "total_activities": current_user_stats.get("total_activities") or 0,
            "avg_deals_per_user": round(avg_deals_per_user, 2),
            "revenue_growth": round(revenue_growth, 2),
        }

        serializer = AnalyticsSummarySerializer(summary_data)
        return Response(
            {
                "success": True,
                "message": f"Analytics summary for last {days} days",
                "data": serializer.data,
            }
        )


class DealAnalyticsListAPIView(ListAPIView):
    """
    List deal analytics with filtering and ordering
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    serializer_class = DealAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date"]
    ordering_fields = ["date", "total_deals", "total_value", "won_deals", "won_value"]
    ordering = ["-date"]

    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            return DealAnalytics.objects.none()

        queryset = DealAnalytics.objects.filter(workspace=workspace)

        # Date range filtering
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Deal analytics retrieved successfully",
                "data": serializer.data,
                "count": len(serializer.data),
            }
        )


class UserAnalyticsListAPIView(ListAPIView):
    """
    List user analytics with filtering and ordering
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    serializer_class = UserAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["user", "date"]
    ordering_fields = [
        "date",
        "deals_created",
        "deals_closed",
        "revenue_generated",
        "activities_completed",
    ]
    ordering = ["-date"]

    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            return UserAnalytics.objects.none()

        queryset = UserAnalytics.objects.filter(workspace=workspace)

        # Date range filtering
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.select_related("user")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "User analytics retrieved successfully",
                "data": serializer.data,
                "count": len(serializer.data),
            }
        )


class UserAnalyticsDetailAPIView(RetrieveAPIView):
    """
    Get detailed analytics for a specific user
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    serializer_class = UserAnalyticsSerializer

    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            return UserAnalytics.objects.none()

        return UserAnalytics.objects.filter(workspace=workspace).select_related("user")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "success": True,
                "message": "User analytics retrieved successfully",
                "data": serializer.data,
            }
        )


class AnalyticsTrendsAPIView(APIView):
    """
    Get analytics trends over time
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {"error": "No active workspace found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get parameters
        days = int(request.query_params.get("days", 30))
        metric = request.query_params.get(
            "metric", "won_value"
        )  # won_value, total_deals, etc.

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Get daily data
        deal_data = (
            DealAnalytics.objects.filter(
                workspace=workspace, date__range=[start_date, end_date]
            )
            .order_by("date")
            .values("date", metric)
        )

        # Format for frontend charts
        trends_data = []
        for item in deal_data:
            trends_data.append(
                {"date": item["date"].isoformat(), "value": item[metric] or 0}
            )

        return Response(
            {
                "success": True,
                "message": f"{metric.replace('_', ' ').title()} trends for last {days} days",
                "data": {"metric": metric, "trends": trends_data, "period_days": days},
            }
        )

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

from leads.models import Lead
from deals.models import Deal
from .serializers import (
    DealAnalyticsSerializer,
    UserAnalyticsSerializer,
    AnalyticsSummarySerializer,
)
from subscriptions.permissions import HasActiveSubscription
from workspaces.utils import get_user_workspace
from workspaces.permissions import IsWorkspaceMember
from django.db.models.functions import TruncDate


class AnalyticsDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response({"error": "No active workspace"}, status=400)

        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        deals = Deal.objects.filter(
            workspace=workspace,
            created_at__date__range=[start_date, end_date],
        )

        leads = Lead.objects.filter(
            workspace=workspace,
            created_at__date__range=[start_date, end_date],
        )

        deal_stats = deals.aggregate(
            total_deals=Count("id"),
            pipeline_value=Sum("value", filter=Q(status="open")),
            won_deals=Count("id", filter=Q(status="won")),
            won_value=Sum("value", filter=Q(status="won")),
            lost_deals=Count("id", filter=Q(status="lost")),
        )

        lead_stats = leads.aggregate(
            total_qualified=Count("id", filter=Q(status="qualified")),
            converted=Count("id", filter=Q(is_converted=True)),
        )

        total_deals = deal_stats["total_deals"] or 0
        won_deals = deal_stats["won_deals"] or 0

        win_rate = (won_deals / total_deals * 100) if total_deals else 0
        conversion_rate = (
            (lead_stats["converted"] / lead_stats["total_qualified"] * 100)
            if lead_stats["total_qualified"]
            else 0
        )

        data = {
            "total_deals": total_deals,
            "total_pipeline_value": deal_stats["pipeline_value"] or 0,
            "won_deals": won_deals,
            "won_value": deal_stats["won_value"] or 0,
            "lost_deals": deal_stats["lost_deals"] or 0,
            "win_rate": round(win_rate, 2),
            "leads_converted": lead_stats["converted"] or 0,
            "conversion_rate": round(conversion_rate, 2),
            "total_qualified_leads": lead_stats["total_qualified"] or 0,
        }

        return Response({"success": True, "data": data})


class DealAnalyticsListAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        qs = Deal.objects.filter(workspace=workspace)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        data = (
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total_deals=Count("id"),
                total_value=Sum("value"),
                won_deals=Count("id", filter=Q(status="won")),
                won_value=Sum("value", filter=Q(status="won")),
            )
            .order_by("-date")
        )

        return Response({"success": True, "data": data})


class UserAnalyticsListAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)
        days = int(request.query_params.get("days", 30))

        start_date = timezone.now().date() - timedelta(days=days)

        data = (
            Deal.objects.filter(
                workspace=workspace,
                created_at__date__gte=start_date,
                assigned_to__isnull=False,
            )
            .values("assigned_to", "assigned_to__email")
            .annotate(
                deals_created=Count("id"),
                deals_won=Count("id", filter=Q(status="won")),
                revenue=Sum("value", filter=Q(status="won")),
            )
        )

        return Response({"success": True, "data": data})


# class UserAnalyticsDetailAPIView(RetrieveAPIView):
#     """
#     Get detailed analytics for a specific user
#     """

#     permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
#     serializer_class = UserAnalyticsSerializer

#     def get_queryset(self):
#         workspace = get_user_workspace(self.request.user)
#         if not workspace:
#             return UserAnalytics.objects.none()

#         return UserAnalytics.objects.filter(workspace=workspace).select_related("user")

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(
#             {
#                 "success": True,
#                 "message": "User analytics retrieved successfully",
#                 "data": serializer.data,
#             }
#         )


class AnalyticsTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)
        days = int(request.query_params.get("days", 30))
        metric = request.query_params.get("metric", "won_value")

        start_date = timezone.now().date() - timedelta(days=days)

        qs = (
            Deal.objects.filter(
                workspace=workspace,
                created_at__date__gte=start_date,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
        )

        if metric == "won_value":
            qs = qs.annotate(value=Sum("value", filter=Q(status="won")))
        elif metric == "total_deals":
            qs = qs.annotate(value=Count("id"))

        return Response(
            {
                "success": True,
                "data": list(qs.order_by("date")),
            }
        )

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from common.swagger import workspace_header


from leads.models import Lead, LeadActivity
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
from django.db.models import Case, When, F, IntegerField, DecimalField
from django.shortcuts import get_object_or_404
from authentication.models import User
from forms.models import Form, FormSubmission
from ...services.time_to_conversion import time_to_conversion_analytics
from ...services.funnel_service import get_user_funnel
from ...services.revenue_service import get_revenue_dashboard
from ...services.dashboard_service import get_dashboard_data
from analytics.models import AutomationAnalytics
from automation.models import AutomationExecutionLog

CACHE_TTL = 300  # seconds, 5 minutes


class AnalyticsDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days",
                type=int,
                description="Number of days for analytics",
                required=False,
            ),
        ],
        responses={200: AnalyticsSummarySerializer},
        description="Get analytics dashboard summary with deals and leads statistics",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response({"error": "No active workspace"}, status=400)

        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        deals = Deal.objects.filter(
            workspace=workspace,
            is_deleted=False,
            created_at__date__range=[start_date, end_date],
        )

        leads = Lead.objects.filter(
            workspace=workspace,
            is_deleted=False,
            created_at__date__range=[start_date, end_date],
        )

        deal_stats = Deal.objects.filter(
            workspace=workspace, is_deleted=False
        ).aggregate(
            total_deals=Count("id"),
            pipeline_value=Sum("value"),
            won_deals=Count(
                Case(
                    When(pipeline_stage="won", then=1),
                    output_field=IntegerField(),
                )
            ),
            won_value=Sum(
                Case(
                    When(pipeline_stage="won", then=F("value")),
                    output_field=DecimalField(),
                )
            ),
            lost_deals=Count(
                Case(
                    When(pipeline_stage="lost", then=1),
                    output_field=IntegerField(),
                )
            ),
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

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="start_date",
                type=str,
                description="Start date (YYYY-MM-DD)",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=str,
                description="End date (YYYY-MM-DD)",
                required=False,
            ),
        ],
        responses={200: DealAnalyticsSerializer(many=True)},
        description="Get daily deal analytics with aggregated metrics",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        qs = Deal.objects.filter(workspace=workspace)
        qs = qs.filter(is_deleted=False)

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
                won_deals=Count(
                    Case(
                        When(pipeline_stage="won", then=1),
                        output_field=IntegerField(),
                    )
                ),
                won_value=Sum(
                    Case(
                        When(pipeline_stage="won", then=F("value")),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("-date")
        )

        return Response({"success": True, "data": data})


class UserAnalyticsListAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days",
                type=int,
                description="Number of days for analytics",
                required=False,
            ),
        ],
        responses={200: UserAnalyticsSerializer(many=True)},
        description="Get user-wise analytics for deals and revenue",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        days = int(request.query_params.get("days", 30))

        start_date = timezone.now().date() - timedelta(days=days)

        data = (
            Deal.objects.filter(
                workspace=workspace,
                is_deleted=False,
                created_at__date__gte=start_date,
                assigned_to__isnull=False,
            )
            .values("assigned_to", "assigned_to__email")
            .annotate(
                deals_created=Count("id"),
                deals_won=Count(
                    Case(
                        When(pipeline_stage="won", then=1),
                        output_field=IntegerField(),
                    )
                ),
                revenue=Sum("value", filter=Q(pipeline_stage="won")),
            )
        )

        return Response({"success": True, "data": data})


class UserAnalyticsDetailAPIView(APIView):
    """
    Returns aggregated analytics for a specific user within the current workspace:
    - Deals created and closed
    - Revenue generated
    - Leads converted
    - Activities completed
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days",
                type=int,
                description="Number of days for analytics",
                required=False,
            ),
        ],
        responses={200: UserAnalyticsSerializer},
        description="Get detailed analytics for a specific user",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request, user_id):
        # 1️⃣ Get current workspace
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {"error": "No active workspace found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2️⃣ Ensure user exists in workspace
        user = get_object_or_404(
            User,
            id=user_id,
            workspace_members__workspace=workspace,
            workspace_members__is_active=True,
        )

        # 3️⃣ Date range
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 4️⃣ Deals stats
        deal_stats = Deal.objects.filter(
            workspace=workspace,
            is_deleted=False,
            assigned_to=user,
            created_at__date__range=[start_date, end_date],
        ).aggregate(
            deals_created=Count("id"),
            deals_closed=Count("id", filter=Q(pipeline_stage="won")),
            revenue_generated=Sum("value", filter=Q(pipeline_stage="won")),
        )

        # 5️⃣ Leads stats (converted)
        # Use 'created_by' + 'is_converted' as per CRM-Buddiz design
        lead_stats = Lead.objects.filter(
            workspace=workspace,
            is_deleted=False,
            created_by=user,
            is_converted=True,
            created_at__date__range=[start_date, end_date],
        ).aggregate(
            leads_converted=Count("id"),  # if field exists
        )

        # 6️⃣ Activities stats
        activity_stats = LeadActivity.objects.filter(
            workspace=workspace,
            is_deleted=False,
            performed_by=user,
            is_completed=True,
            created_at__date__range=[start_date, end_date],
        ).aggregate(activities_completed=Count("id"))

        # 7️⃣ Response
        data = {
            "user_id": user.id,
            "user_name": user.full_name,
            "period_days": days,
            "deals_created": deal_stats.get("deals_created") or 0,
            "deals_closed": deal_stats.get("deals_closed") or 0,
            "revenue_generated": deal_stats.get("revenue_generated") or 0,
            "leads_converted": lead_stats.get("leads_converted") or 0,
            "conversion_value": lead_stats.get("conversion_value") or 0,
            "activities_completed": activity_stats.get("activities_completed") or 0,
        }

        return Response(
            {
                "success": True,
                "message": "User analytics retrieved successfully",
                "data": data,
            }
        )


class AnalyticsTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
            OpenApiParameter(
                name="metric",
                type=str,
                description="Metric type (won_value, total_deals)",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="Trend data")},
        description="Get analytics trends over time",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
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
            qs = qs.annotate(value=Sum("value", filter=Q(pipeline_stage="won")))
        elif metric == "total_deals":
            qs = qs.annotate(value=Count("id"))

        return Response(
            {
                "success": True,
                "data": list(qs.order_by("date")),
            }
        )


class FormTrendAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Form submission trends")},
        description="Get form submission trends over time",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        data = (
            FormSubmission.objects.filter(form=form)
            .annotate(date=TruncDate("submitted_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return Response(data)


class FormConversionFunnelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
        ],
        responses={200: OpenApiResponse(description="Form conversion funnel data")},
        description="Get conversion funnel analytics for a specific form",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 🔹 submissions
        submissions_qs = FormSubmission.objects.filter(
            form=form,
            submitted_at__date__range=[start_date, end_date],
        )

        submissions_count = submissions_qs.count()

        # 🔹 leads
        lead_ids = submissions_qs.exclude(lead=None).values_list("lead_id", flat=True)

        leads_count = len(set(lead_ids))

        # 🔹 deals
        deals_qs = Deal.objects.filter(
            workspace=workspace,
            created_from_lead_id__in=lead_ids,
        )

        deals_count = deals_qs.count()

        # 🔹 won deals
        won_qs = deals_qs.filter(pipeline_stage="won")
        won_count = won_qs.count()

        revenue = won_qs.aggregate(total=Sum("value"))["total"] or 0

        # 🔹 conversion rates
        submission_to_lead = (
            (leads_count / submissions_count) * 100 if submissions_count else 0
        )

        lead_to_deal = (deals_count / leads_count) * 100 if leads_count else 0

        deal_to_won = (won_count / deals_count) * 100 if deals_count else 0

        return Response(
            {
                "form_id": form.id,
                "form_name": form.name,
                "period_days": days,
                "submissions": submissions_count,
                "leads": leads_count,
                "deals": deals_count,
                "won": won_count,
                "revenue": revenue,
                "rates": {
                    "submission_to_lead": round(submission_to_lead, 2),
                    "lead_to_deal": round(lead_to_deal, 2),
                    "deal_to_won": round(deal_to_won, 2),
                },
            }
        )


class UserConversionFunnelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="User funnel analytics")},
        description="Get conversion funnel analytics for current user",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        if not workspace:
            return Response({"error": "No workspace"}, status=400)

        data = get_user_funnel(workspace)

        return Response(
            {
                "success": True,
                "message": "User funnel analytics",
                "data": data,
            }
        )


class WorkspaceFunnelDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
        ],
        responses={200: OpenApiResponse(description="Workspace funnel dashboard data")},
        description="Get comprehensive workspace funnel dashboard with conversion metrics",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        if not workspace:
            return Response(
                {"error": "No active workspace"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # submissions
        submissions_qs = FormSubmission.objects.filter(
            workspace=workspace,
            submitted_at__date__range=[start_date, end_date],
        )

        submissions_count = submissions_qs.count()

        # leads
        lead_ids = submissions_qs.exclude(lead=None).values_list("lead_id", flat=True)

        unique_lead_ids = list(set(lead_ids))
        leads_count = len(unique_lead_ids)

        # deals
        deals_qs = Deal.objects.filter(
            workspace=workspace,
            created_from_lead_id__in=unique_lead_ids,
        )

        deals_count = deals_qs.count()

        # won deals
        won_qs = deals_qs.filter(pipeline_stage="won")
        won_count = won_qs.count()

        revenue = won_qs.aggregate(total=Sum("value"))["total"] or 0

        # rates
        submission_to_lead = (
            (leads_count / submissions_count) * 100 if submissions_count else 0
        )

        lead_to_deal = (deals_count / leads_count) * 100 if leads_count else 0

        deal_to_won = (won_count / deals_count) * 100 if deals_count else 0

        # top forms
        top_forms = (
            FormSubmission.objects.filter(
                workspace=workspace,
                submitted_at__date__range=[start_date, end_date],
            )
            .values("form_id", "form__name")
            .annotate(submissions=Count("id"))
            .order_by("-submissions")[:5]
        )

        top_form_data = []

        for form in top_forms:
            form_leads = (
                FormSubmission.objects.filter(form_id=form["form_id"])
                .exclude(lead=None)
                .values_list("lead_id", flat=True)
            )

            form_deals = Deal.objects.filter(
                workspace=workspace, created_from_lead_id__in=form_leads
            )

            form_revenue = (
                form_deals.filter(pipeline_stage="won").aggregate(total=Sum("value"))[
                    "total"
                ]
                or 0
            )

            top_form_data.append(
                {
                    "form_id": form["form_id"],
                    "form_name": form["form__name"],
                    "submissions": form["submissions"],
                    "deals": form_deals.count(),
                    "revenue": form_revenue,
                }
            )

        return Response(
            {
                "period_days": days,
                "submissions": submissions_count,
                "leads": leads_count,
                "deals": deals_count,
                "won": won_count,
                "revenue": revenue,
                "rates": {
                    "submission_to_lead": round(submission_to_lead, 2),
                    "lead_to_deal": round(lead_to_deal, 2),
                    "deal_to_won": round(deal_to_won, 2),
                },
                "top_forms": top_form_data,
            }
        )


class TimeToConversionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
        ],
        responses={200: OpenApiResponse(description="Time to conversion analytics")},
        description="Get time-to-conversion analytics",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        if not workspace:
            return Response({"error": "No workspace found"}, status=400)

        days = int(request.query_params.get("days", 30))

        data = time_to_conversion_analytics(workspace, days)

        return Response(
            {
                "success": True,
                "message": "Time-to-conversion analytics",
                "data": data,
            }
        )


class RevenueDashboardAPIView(APIView):
    """Returns a dashboard of revenue metrics"""

    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
        ],
        responses={200: OpenApiResponse(description="Revenue dashboard data")},
        description="Get revenue dashboard with financial metrics",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        if not workspace:
            return Response({"error": "No workspace"}, status=400)

        days = int(request.query_params.get("days", 30))

        data = get_revenue_dashboard(workspace, days)

        return Response(
            {
                "success": True,
                "message": "Revenue dashboard",
                "data": data,
            }
        )


class UnifiedDashboardAPIView(APIView):
    """
    Returns a full workspace analytics dashboard in real-time.
    Works seamlessly with batched signals and cache invalidation.
    """

    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="days", type=int, description="Number of days", required=False
            ),
        ],
        responses={200: OpenApiResponse(description="Unified dashboard data")},
        description="Get unified workspace analytics dashboard with cached data",
        tags=["Analytics"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response({"error": "No workspace found"}, status=400)

        days = int(request.query_params.get("days", 30))

        cache_key = f"dashboard_workspace_{workspace.id}_days_{days}"
        data = cache.get(cache_key)
        if not data:
            # Rebuild dashboard fresh if cache missing or invalidated
            data = get_dashboard_data(workspace, days)
            cache.set(cache_key, data, CACHE_TTL)

        return Response(
            {
                "success": True,
                "message": "Unified dashboard retrieved successfully",
                "data": data,
            }
        )


# =====================================================


class AutomationDashboardAPIView(APIView):
    """Returns a dashboard of automation metrics"""

    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Automation dashboard data")},
        description="Get automation dashboard with metrics",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        data = AutomationAnalytics.objects.filter(workspace=workspace).order_by(
            "-date"
        )[:30]

        return Response(
            [
                {
                    "date": d.date,
                    "total": d.total_executions,
                    "success": d.success_count,
                    "failed": d.failed_count,
                }
                for d in data
            ]
        )


class AutomationRulePerformanceAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Automation rule performance data")
        },
        description="Get performance metrics for each automation rule",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)

        logs = (
            AutomationExecutionLog.objects.filter(workspace=workspace)
            .values("rule__id", "rule__name")
            .annotate(
                total=Count("id"),
                success=Count("id", filter=Q(status="success")),
                failed=Count("id", filter=Q(status="failed")),
            )
        )

        return Response(logs)

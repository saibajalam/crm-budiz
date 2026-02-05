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
from accounts.models import User
from forms.models import Form, FormSubmission


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
            created_by=user,
            is_converted=True,
            created_at__date__range=[start_date, end_date],
        ).aggregate(
            leads_converted=Count("id"),  # if field exists
        )

        # 6️⃣ Activities stats
        activity_stats = LeadActivity.objects.filter(
            workspace=workspace,
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


class FormAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request, form_id):
        workspace = get_user_workspace(request.user)

        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        submissions = FormSubmission.objects.filter(form=form)

        total_submissions = submissions.count()

        leads = submissions.exclude(lead=None).values_list("lead_id", flat=True)

        total_leads = len(leads)
        unique_leads = len(set(leads))

        deals = Deal.objects.filter(workspace=workspace, lead_id__in=leads)

        deals_created = deals.count()

        revenue = (
            deals.filter(pipeline_stage="won").aggregate(total=Sum("value"))["total"]
            or 0
        )

        conversion_rate = 0
        if total_submissions > 0:
            conversion_rate = (deals_created / total_submissions) * 100

        return Response(
            {
                "form_name": form.name,
                "submissions": total_submissions,
                "leads_created": total_leads,
                "unique_leads": unique_leads,
                "deals_created": deals_created,
                "revenue": revenue,
                "conversion_rate": round(conversion_rate, 2),
            }
        )


class FormTrendAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

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


class WorkspaceFormsAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)

        forms = Form.objects.filter(workspace=workspace)

        results = []

        for form in forms:
            submissions = FormSubmission.objects.filter(form=form)
            count = submissions.count()

            leads = submissions.exclude(lead=None).count()

            results.append(
                {
                    "form_id": form.id,
                    "form_name": form.name,
                    "submissions": count,
                    "leads": leads,
                }
            )

        return Response(results)

from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from common.api_response import api_response
from leads.models import Lead, LeadActivity
from deals.models import Deal, DealActivity, DealContact
from deals.api.v1.querysets import get_workspace_deal_activity_queryset
from contact.models import Contact
from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace


class GlobalActivityItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    entity = serializers.CharField()
    entity_id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    performed_by = serializers.IntegerField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()


class GlobalActivityResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = GlobalActivityItemSerializer(many=True)
    message = serializers.CharField()
    error = serializers.BooleanField()


class GlobalSearchResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.JSONField()
    message = serializers.CharField()
    error = serializers.BooleanField()


class GlobalActivityListAPIView(APIView):
    serializer_class = GlobalActivityResponseSerializer
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        operation_id="activities_list",
        responses={200: GlobalActivityResponseSerializer},
        tags=["Activities"],
        parameters=[
            OpenApiParameter("type", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("user", int, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("start_date", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("end_date", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("entity", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("contact_id", int, OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        workspace = getattr(request, "workspace", None) or get_user_workspace(request.user)
        if not workspace:
            return api_response(
                data=[],
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        activity_type = request.query_params.get("type")
        user_id = request.query_params.get("user")
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))
        entity = request.query_params.get("entity")
        contact_id = request.query_params.get("contact_id")

        records = []

        include_deal = entity in (None, "", "deal", "contact")
        include_lead = entity in (None, "", "lead")

        if include_deal:
            deal_qs = get_workspace_deal_activity_queryset(
                workspace=workspace,
                activity_type=activity_type,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )
            if entity == "contact" and contact_id:
                deal_ids = DealContact.objects.filter(
                    workspace=workspace,
                    contact_id=contact_id,
                    is_deleted=False,
                ).values_list("deal_id", flat=True)
                deal_qs = deal_qs.filter(deal_id__in=deal_ids)

            for item in deal_qs.select_related("deal", "assigned_to")[:200]:
                records.append(
                    {
                        "id": item.id,
                        "entity": "deal",
                        "entity_id": item.deal_id,
                        "type": item.activity_type,
                        "title": item.title,
                        "description": item.description,
                        "performed_by": item.assigned_to_id,
                        "created_at": item.created_at,
                    }
                )

        if include_lead:
            lead_qs = LeadActivity.objects.filter(workspace=workspace, is_deleted=False)
            if activity_type:
                lead_qs = lead_qs.filter(activity_type__iexact=activity_type)
            if user_id:
                lead_qs = lead_qs.filter(performed_by_id=user_id)
            if start_date:
                lead_qs = lead_qs.filter(created_at__date__gte=start_date)
            if end_date:
                lead_qs = lead_qs.filter(created_at__date__lte=end_date)

            for item in lead_qs.select_related("lead", "performed_by")[:200]:
                records.append(
                    {
                        "id": item.id,
                        "entity": "lead",
                        "entity_id": item.lead_id,
                        "type": item.activity_type,
                        "title": item.subject,
                        "description": item.description,
                        "performed_by": item.performed_by_id,
                        "created_at": item.created_at,
                    }
                )

        records.sort(key=lambda x: x["created_at"], reverse=True)

        return api_response(
            data=records,
            message="Activities fetched successfully",
            status_code=status.HTTP_200_OK,
        )


class GlobalSearchAPIView(APIView):
    serializer_class = GlobalSearchResponseSerializer
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        operation_id="search_global",
        responses={200: GlobalSearchResponseSerializer},
        tags=["Search"],
        parameters=[
            OpenApiParameter("q", str, OpenApiParameter.QUERY, required=True),
        ],
    )
    def get(self, request):
        workspace = getattr(request, "workspace", None) or get_user_workspace(request.user)
        if not workspace:
            return api_response(
                data={"deals": [], "contacts": [], "leads": [], "activities": []},
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        q = (request.query_params.get("q") or "").strip()
        if not q:
            return api_response(
                data={"deals": [], "contacts": [], "leads": [], "activities": []},
                message="Search query is required",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        deals = (
            Deal.objects.filter(workspace=workspace, is_deleted=False)
            .filter(Q(title__icontains=q) | Q(notes__icontains=q))
            .values("id", "title", "value", "pipeline_stage")[:20]
        )
        contacts = (
            Contact.objects.filter(workspace=workspace, is_deleted=False)
            .filter(Q(name__icontains=q) | Q(email__icontains=q))
            .values("id", "name", "email", "phone")[:20]
        )
        leads = (
            Lead.objects.filter(workspace=workspace, is_deleted=False)
            .filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(company__icontains=q)
            )
            .values("id", "first_name", "last_name", "email", "status")[:20]
        )

        lead_activities = (
            LeadActivity.objects.filter(workspace=workspace, is_deleted=False)
            .filter(Q(subject__icontains=q) | Q(description__icontains=q))
            .values("id", "activity_type", "subject", "lead_id")[:10]
        )
        deal_activities = (
            DealActivity.objects.filter(workspace=workspace, is_deleted=False)
            .filter(Q(title__icontains=q) | Q(description__icontains=q))
            .values("id", "activity_type", "title", "deal_id")[:10]
        )

        activities = [
            {
                "id": item["id"],
                "entity": "lead",
                "entity_id": item["lead_id"],
                "type": item["activity_type"],
                "title": item["subject"],
            }
            for item in lead_activities
        ]
        activities.extend(
            {
                "id": item["id"],
                "entity": "deal",
                "entity_id": item["deal_id"],
                "type": item["activity_type"],
                "title": item["title"],
            }
            for item in deal_activities
        )

        return api_response(
            data={
                "deals": list(deals),
                "contacts": list(contacts),
                "leads": list(leads),
                "activities": activities,
            },
            message="Search completed successfully",
            status_code=status.HTTP_200_OK,
        )

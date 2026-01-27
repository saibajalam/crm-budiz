from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Lead, LeadActivity, LeadActivityAttachment
from .serializers import (
    CreateLeadSerializer,
    LeadActivityCreateSerializer,
    LeadActivityUpdateSerializer,
    LeadListSerializer,
    LeadDetailSerializer,
    LeadActivityListSerializer,
    LeadUpdateSerializer,
)
from subscriptions.permissions import HasActiveSubscription
from .permissions import CanDeleteLead, CanDeleteLeadActivity
from core.pagination import LeadPagination
from leads.utils import update_lead_score
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from workspaces.utils import get_user_workspace
from workspaces.permissions import IsWorkspaceMember, IsWorkspaceOwnerOrAdmin
from common.utils import format_display_number


# -------------------
# Leads
# -------------------
class LeadListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    queryset = Lead.objects.all()
    serializer_class = LeadListSerializer
    pagination_class = LeadPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["first_name", "last_name", "email", "phone", "company"]
    filterset_fields = ["status", "source"]
    ordering_fields = ["created_at", "score"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Lead.objects.filter(workspace_members_user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLeadSerializer
        return LeadListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(
            {
                "message": "Leads retrieved successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": 200,
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {
                    "message": "No active workspace found",
                    "success": False,
                    "error": True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = serializer.save(
            workspace=workspace,
            created_by=request.user,
        )

        return Response(
            {
                "message": "Lead created successfully",
                "data": {
                    "id": lead.id,
                    "display_number": lead.display_number,
                    "formatted_number": format_display_number(
                        "LEAD", lead.display_number
                    ),
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "status": lead.status,
                    "source": lead.source,
                    "workspace_id": lead.workspace_id,
                    "created_by_id": lead.created_by_id,
                },
                "success": True,
                "error": None,
                "status_code": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


class LeadRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription,
        CanDeleteLead,
        IsWorkspaceOwnerOrAdmin,
    ]
    queryset = Lead.objects.all()
    lookup_url_kwarg = "lead_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LeadUpdateSerializer
        return LeadDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        lead = self.get_object()
        serializer = self.get_serializer(lead)
        return Response(
            {
                "message": "Lead retrieved successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = LeadDetailSerializer(
            instance, context={"request": request}
        )
        return Response(
            {
                "message": "Lead updated successfully",
                "data": response_serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        lead = self.get_object()
        lead.soft_delete()
        return Response(
            {
                "message": "Lead deleted successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def restore(self, request, *args, **kwargs):
        lead = self.get_object()
        lead.restore()
        return Response(
            {
                "message": "Lead restored successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class LeadRestoreAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription,
        IsWorkspaceMember,
    ]  # can add custom permission if needed

    def post(self, request, lead_id):
        try:
            lead = Lead.all_objects.get(id=lead_id, is_deleted=True)
        except Lead.DoesNotExist:
            return Response(
                {
                    "message": "Lead not found or not deleted",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Optional: Only creator/admin/superadmin can restore
        if not (request.user == lead.created_by or request.user.is_staff):
            return Response(
                {
                    "message": "You do not have permission to restore this lead",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        lead.restore()

        return Response(
            {
                "message": "Lead restored successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


# -------------------
# Lead Activities
# -------------------


class LeadActivityListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    serializer_class = LeadActivityListSerializer
    pagination_class = LeadPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        lead_id = self.kwargs["lead_id"]
        get_object_or_404(Lead, id=lead_id)
        return (
            LeadActivity.objects.filter(lead_id=lead_id)
            .select_related("performed_by")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeadActivityCreateSerializer
        return LeadActivityListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(
            {
                "message": "Lead activities retrieved successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            }
        )

    def perform_create(self, serializer):
        lead = get_object_or_404(Lead, id=self.kwargs["lead_id"])
        activity = LeadActivity.objects.create(
            lead=lead,
            activity_type=serializer.validated_data["activity_type"],
            priority=serializer.validated_data.get("priority", "medium"),
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data.get("description", ""),
            due_date=serializer.validated_data.get("due_date"),
            attachment=serializer.validated_data.get("attachment"),
            performed_by=self.request.user,
        )
        # Update lead score
        update_lead_score(lead, activity.activity_type)
        serializer.instance = (
            activity  # required if you want serializer.instance for later
        )

        return Response(
            {
                "success": True,
                "message": "Activity created successfully",
                "data": {"activity_id": activity.id, "lead_score": lead.score},
                "error": None,
                "status": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


class LeadActivityRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription,
        CanDeleteLeadActivity,
        IsWorkspaceMember,
    ]
    queryset = LeadActivity.objects.all()
    lookup_url_kwarg = "activity_id"
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LeadActivityUpdateSerializer
        return LeadActivityListSerializer

    def retrieve(self, request, *args, **kwargs):
        activity = self.get_object()
        serializer = self.get_serializer(activity)
        return Response(
            {
                "message": "Lead activity retrieved successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        activity = self.get_object()
        serializer = self.get_serializer(activity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Save attachments
        attachments = request.FILES.getlist("attachments")
        for file in attachments:
            LeadActivityAttachment.objects.create(activity=activity, file=file)

        return Response(
            {
                "message": "Lead activity updated successfully",
                "data": {
                    "activity_id": activity.id,
                    "attachments_added": len(attachments),
                },
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        activity = self.get_object()
        activity.soft_delete()
        return Response(
            {
                "message": "Lead activity deleted successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    def restore(self, request, *args, **kwargs):
        activity = self.get_object()
        activity.restore()
        return Response(
            {
                "message": "Activity restored successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class LeadActivityRestoreAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    def post(self, request, activity_id):
        try:
            activity = LeadActivity.all_objects.get(id=activity_id, is_deleted=True)
        except LeadActivity.DoesNotExist:
            return Response(
                {
                    "message": "Activity not found or not deleted",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not (request.user == activity.performed_by or request.user.is_staff):
            return Response(
                {
                    "message": "You do not have permission to restore this activity",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        activity.restore()

        return Response(
            {
                "message": "Activity restored successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

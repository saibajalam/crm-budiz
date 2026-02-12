from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from ...models import Lead, LeadActivity, LeadActivityAttachment
from .serializers import (
    CreateLeadSerializer,
    LeadActivityCreateSerializer,
    LeadActivityUpdateSerializer,
    LeadListSerializer,
    LeadDetailSerializer,
    LeadActivityListSerializer,
    LeadUpdateSerializer,
    LeadActivityFeedSerializer,
    LeadConversionSerializer,
)
from subscriptions.permissions import HasActiveSubscription
from ...permissions import CanDeleteLead, CanDeleteLeadActivity, LeadAccessPermission
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
        workspace = get_user_workspace(self.request.user)
        return Lead.objects.filter(workspace=workspace)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLeadSerializer
        return LeadListSerializer

    @extend_schema(
        operation_id="API To GET leads",
        description="""
        This API is to retrieve the details of leads provided in the URL.
        """,
        summary="EP-LEAD-01",
        request=LeadListSerializer,
    )
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

    @extend_schema(
        operation_id="API To CREATE individual lead",
        description="""
        This API is to create a new lead.
        """,
        summary="EP-LEAD-02",
        request=CreateLeadSerializer,
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

        response_serializer = LeadDetailSerializer(lead, context={"request": request})
        return Response(
            {
                "message": "Lead created successfully",
                "data": response_serializer.data,
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
        LeadAccessPermission,
    ]
    queryset = Lead.objects.all()
    lookup_url_kwarg = "lead_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LeadUpdateSerializer
        return LeadDetailSerializer

    @extend_schema(
        operation_id="API To GET individual lead",
        description="""
        This API is to retrieve the details of an individual lead.
        """,
        summary="EP-LEAD-03",
        request=LeadDetailSerializer,
    )
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

    @extend_schema(
        operation_id="API To UPDATE individual lead",
        description="""
        This API is to update an existing lead.
        """,
        summary="EP-LEAD-04",
        request=LeadUpdateSerializer,
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

    @extend_schema(
        operation_id="API To DELETE individual lead",
        description="""
        This API is to delete an existing lead.
        """,
        summary="EP-LEAD-05",
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


class LeadRestoreAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription,
        IsWorkspaceMember,
    ]  # can add custom permission if needed

    @extend_schema(
        operation_id="API To RESTORE individual lead",
        description="""
        This API is to restore a deleted lead.
        """,
        summary="EP-LEADRESTORE-01",
    )
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
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            raise PermissionDenied("You are not permitted to perform this action")

        try:
            get_object_or_404(Lead, id=lead_id, workspace=workspace)
        except Exception:
            raise PermissionDenied("You are not permitted to perform this action")
        return (
            LeadActivity.objects.filter(lead_id=lead_id, workspace=workspace)
            .select_related("performed_by")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeadActivityCreateSerializer
        return LeadActivityListSerializer

    @extend_schema(
        operation_id="API To GET lead-related activites",
        description="""
        This API is to retrieve lead-related activities.
        """,
        summary="EP-LEADACTIVITY-01",
        request=LeadActivityListSerializer,
    )
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

    @extend_schema(
        operation_id="API To CREATE lead-related activity",
        description="""
        This API is to create a new lead-related activity.
        """,
        summary="EP-LEADACTIVITY-02",
        request=LeadActivityCreateSerializer,
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead_id = self.kwargs["lead_id"]
        workspace = get_user_workspace(request.user)
        if not workspace:
            raise PermissionDenied("You are not permitted to perform this action")

        requested_lead_id = serializer.validated_data.get("lead_id")
        if requested_lead_id is not None and requested_lead_id != lead_id:
            return Response(
                {
                    "success": False,
                    "message": "Lead ID in request does not match URL",
                    "data": None,
                    "error": True,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lead = get_object_or_404(Lead, id=lead_id, workspace=workspace)
        except Exception:
            raise PermissionDenied("You are not permitted to perform this action")

        with transaction.atomic():
            activity = LeadActivity.objects.create(
                lead=lead,
                workspace=lead.workspace,
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

            # Return activity data using the list serializer
            response_serializer = LeadActivityListSerializer(
                activity, context={"request": request}
            )

            return Response(
                {
                    "success": True,
                    "message": "Activity created successfully",
                    "data": response_serializer.data,
                    "error": None,
                    "status_code": status.HTTP_201_CREATED,
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

    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            raise PermissionDenied("You are not permitted to perform this action")

        return LeadActivity.objects.filter(workspace=workspace)

    def get_object(self):
        obj = super().get_object()
        workspace = get_user_workspace(self.request.user)
        if not workspace or obj.workspace_id != workspace.id:
            raise PermissionDenied("You are not permitted to perform this action")
        return obj

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LeadActivityUpdateSerializer
        return LeadActivityListSerializer

    @extend_schema(
        operation_id="API To RETRIEVE a specific lead-related activity",
        description="""
        This API is to retrieve a specific lead-related activity.
        """,
        summary="EP-LEADACTIVITY-03",
        request=LeadActivityListSerializer,
    )
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

    @extend_schema(
        operation_id="API To UPDATE lead-related activity",
        description="""
        This API is to update a specific lead-related activity.
        """,
        summary="EP-LEADACTIVITY-04",
        request=LeadActivityUpdateSerializer,
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

        response_serializer = LeadActivityListSerializer(
            activity, context={"request": request}
        )

        return Response(
            {
                "message": "Lead activity updated successfully",
                "data": response_serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="API To DELETE lead-related activity",
        description="""
        This API is to delete a specific lead-related activity.
        """,
        summary="EP-LEADACTIVITY-05",
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


class LeadActivityRestoreAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        operation_id="API To RESTORE lead-related activity",
        description="""
        This API is to restore a specific lead-related activity.
        """,
        summary="EP-LEADACTIVITY-06",
    )
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


class LeadActivityFeedAPIView(ListAPIView):

    serializer_class = LeadActivityFeedSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, LeadAccessPermission]

    def get_queryset(self):
        user = self.request.user
        workspace = get_user_workspace(user)
        if not workspace:
            return LeadActivity.objects.none()

        lead_id = self.kwargs.get("lead_id")
        queryset = LeadActivity.objects.filter(
            lead_id=lead_id, lead__workspace=workspace
        )

        category = self.request.query_params.get("category")
        if category == "upcoming":
            queryset = queryset.filter(due_date__gt=timezone.now(), is_completed=False)
        elif category == "overdue":
            queryset = queryset.filter(due_date__lt=timezone.now(), is_completed=False)
        elif category == "completed":
            queryset = queryset.filter(is_completed=True)

        return queryset.order_by("-due_date")

    @extend_schema(
        operation_id="API To GET lead-related activites",
        description="""
        This API is to retrieve lead-related activities.
        """,
        summary="EP-LEADACTIVITY-07",
        request=LeadActivityListSerializer,
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "Activities feed retrieved successfully",
                "status_code": status.HTTP_200_OK,
            }
        )


# -------------------
# Lead Conversion
# -------------------
class LeadConversionAPIView(APIView):
    """
    Convert a qualified lead to a deal.
    POST /api/v1/leads/{lead_id}/convert/
    """

    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        operation_id="API To CONVERT lead to deal",
        description="""
        This API is to convert a qualified lead to a deal.
        """,
        summary="EP-LEADCONVERSION-01",
        request=LeadConversionSerializer,
    )
    @transaction.atomic
    def post(self, request, lead_id):
        # Get workspace
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {
                    "message": "No active workspace found",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get and validate lead
        try:
            lead = Lead.objects.get(id=lead_id, workspace=workspace, is_deleted=False)
        except Lead.DoesNotExist:
            return Response(
                {
                    "message": "Lead not found or access denied",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Use the conversion serializer

        serializer = LeadConversionSerializer(
            data=request.data,
            context={"request": request, "workspace": workspace, "lead": lead},
        )

        if serializer.is_valid():
            try:
                deal = serializer.save()

                # Return success response with deal details
                return Response(
                    {
                        "message": f"Lead '{lead.first_name} {lead.last_name}' successfully converted to deal",
                        "data": {
                            "deal_id": deal.id,
                            "deal_title": deal.title,
                            "lead_id": lead.id,
                            "activities_transferred": lead.activities.filter(
                                is_deleted=False
                            ).count(),
                        },
                        "success": True,
                        "error": False,
                        "status_code": status.HTTP_201_CREATED,
                    },
                    status=status.HTTP_201_CREATED,
                )

            except Exception as e:
                return Response(
                    {
                        "message": f"Conversion failed: {str(e)}",
                        "data": None,
                        "success": False,
                        "error": True,
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "message": "Validation failed",
                "data": serializer.errors,
                "success": False,
                "error": True,
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from common.swagger import workspace_header
from django.db import transaction

from deals.models import Deal, DealActivity
from .serializers import (
    CreateDealSerializer,
    DealDetailSerializer,
    DealUpdateSerializer,
    DealPipelineSerializer,
    DealAssignmentSerializer,
    DealActivityFeedSerializer,
    CreateDealActivitySerializer,
    UpdateDealActivitySerializer,
    DealContactSerializer,
)
from subscriptions.permissions import HasActiveSubscription
from ...permissions import CanAssignDeal, DealAccessPermission
from rest_framework.exceptions import PermissionDenied
from workspaces.utils import get_user_workspace
from django.shortcuts import get_object_or_404
from workspaces.permissions import IsWorkspaceMember, IsWorkspaceOwnerOrAdmin
from common.utils import format_display_number
from django.utils import timezone
from django.db import transaction
from core.pagination import LeadPagination
from common.api_response import api_response
from common.eventing import emit_crm_event
from workspaces.models import WorkspaceMember
from deals.models import DealContact
from django_filters.rest_framework import DjangoFilterBackend
from .querysets import get_workspace_deal_activity_queryset


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.none()
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]
    pagination_class = LeadPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["title", "notes"]
    ordering_fields = ["created_at", "value", "expected_close_date"]
    ordering = ["-created_at"]

    def _workspace(self):
        return getattr(self.request, "workspace", None) or get_user_workspace(
            self.request.user
        )

    def _is_admin(self, workspace, user):
        if workspace and workspace.owner_id == user.id:
            return True
        return WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
            role__in=["admin", "owner"],
            is_active=True,
        ).exists()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Deal.objects.none()

        if not getattr(self.request.user, "is_authenticated", False):
            return Deal.objects.none()

        workspace = self._workspace()
        if not workspace:
            return Deal.objects.none()

        queryset = Deal.objects.filter(workspace=workspace, is_deleted=False)

        stage = self.request.query_params.get("stage")
        assigned_user = self.request.query_params.get("assigned_to")
        min_value = self.request.query_params.get("min_value")
        max_value = self.request.query_params.get("max_value")

        if stage:
            queryset = queryset.filter(pipeline_stage__iexact=stage)
        if assigned_user:
            queryset = queryset.filter(assigned_to_id=assigned_user)
        if min_value:
            queryset = queryset.filter(value__gte=min_value)
        if max_value:
            queryset = queryset.filter(value__lte=max_value)

        return queryset.select_related("assigned_to", "workspace")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateDealSerializer
        if self.action in ["update", "partial_update"]:
            return DealUpdateSerializer
        return DealDetailSerializer

    def create(self, request, *args, **kwargs):
        workspace = self._workspace()
        if not workspace:
            return api_response(
                data=None,
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "workspace": workspace},
        )
        serializer.is_valid(raise_exception=True)
        deal = serializer.save()

        emit_crm_event(
            event_name="deal.created",
            workspace=workspace,
            payload={"entity_id": deal.id, "updated_fields": list(request.data.keys())},
            user=request.user,
        )

        return api_response(
            data=DealDetailSerializer(deal, context={"request": request}).data,
            message="Deal created successfully",
            status_code=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = DealDetailSerializer(page, many=True, context={"request": request})
            paginated = self.get_paginated_response(serializer.data).data
            return api_response(
                data=paginated,
                message="Deals fetched successfully",
                status_code=status.HTTP_200_OK,
            )

        serializer = DealDetailSerializer(queryset, many=True, context={"request": request})
        return api_response(
            data=serializer.data,
            message="Deals fetched successfully",
            status_code=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        deal = self.get_object()
        return api_response(
            data=DealDetailSerializer(deal, context={"request": request}).data,
            message="Deal details fetched successfully",
            status_code=status.HTTP_200_OK,
        )

    def partial_update(self, request, *args, **kwargs):
        deal = self.get_object()
        workspace = self._workspace()

        is_assigned_user = deal.assigned_to_id == request.user.id
        if not (is_assigned_user or self._is_admin(workspace, request.user)):
            raise PermissionDenied("Only assigned users or admins can edit this deal.")

        serializer = self.get_serializer(deal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        changed_fields = list(request.data.keys())
        if changed_fields:
            DealActivity.objects.create(
                deal=deal,
                workspace=workspace,
                title=f"Deal updated: {', '.join(changed_fields)}",
                description="Deal fields were updated",
                due_date=timezone.now(),
                status="completed",
                activity_type="STATUS_CHANGE",
                assigned_to=request.user,
            )

        emit_crm_event(
            event_name="deal.updated",
            workspace=workspace,
            payload={"entity_id": deal.id, "updated_fields": changed_fields},
            user=request.user,
        )

        return api_response(
            data=DealDetailSerializer(deal, context={"request": request}).data,
            message="Deal updated successfully",
            status_code=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        deal = self.get_object()
        deal.soft_delete()

        emit_crm_event(
            event_name="deal.deleted",
            workspace=deal.workspace,
            payload={"entity_id": deal.id, "updated_fields": ["is_deleted"]},
            user=request.user,
        )

        return api_response(
            data=None,
            message="Deal deleted successfully",
            status_code=status.HTTP_200_OK,
        )


class DealContactListCreateAPIView(APIView):
    serializer_class = DealContactSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        operation_id="deal_contacts_list",
        responses={200: DealContactSerializer(many=True)},
        tags=["Deal Contacts"],
        parameters=[workspace_header],
    )
    def get(self, request, deal_id):
        workspace = getattr(request, "workspace", None) or get_user_workspace(request.user)
        if not workspace:
            return api_response(
                data=None,
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        deal = get_object_or_404(Deal, id=deal_id, workspace=workspace, is_deleted=False)
        relations = DealContact.objects.filter(
            deal=deal, workspace=workspace, is_deleted=False
        ).select_related("contact")
        serializer = DealContactSerializer(relations, many=True)
        return api_response(
            data=serializer.data,
            message="Deal contacts fetched successfully",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="deal_contacts_create",
        request=DealContactSerializer,
        responses={201: DealContactSerializer},
        tags=["Deal Contacts"],
        parameters=[workspace_header],
    )
    def post(self, request, deal_id):
        workspace = getattr(request, "workspace", None) or get_user_workspace(request.user)
        if not workspace:
            return api_response(
                data=None,
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        deal = get_object_or_404(Deal, id=deal_id, workspace=workspace, is_deleted=False)
        serializer = DealContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact = serializer.validated_data["contact"]
        relation, _ = DealContact.objects.update_or_create(
            deal=deal,
            contact=contact,
            defaults={
                "workspace": workspace,
                "role": serializer.validated_data.get("role", ""),
                "is_primary": serializer.validated_data.get("is_primary", False),
                "is_deleted": False,
            },
        )

        if relation.is_primary:
            DealContact.objects.filter(deal=deal, workspace=workspace).exclude(
                id=relation.id
            ).update(is_primary=False)

        return api_response(
            data=DealContactSerializer(relation).data,
            message="Contact linked to deal successfully",
            status_code=status.HTTP_201_CREATED,
        )


class DealContactDeleteAPIView(APIView):
    serializer_class = DealContactSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        operation_id="deal_contacts_delete",
        responses={200: OpenApiResponse(description="Contact unlinked from deal")},
        tags=["Deal Contacts"],
        parameters=[workspace_header],
    )
    def delete(self, request, deal_id, contact_id):
        workspace = getattr(request, "workspace", None) or get_user_workspace(request.user)
        if not workspace:
            return api_response(
                data=None,
                message="No active workspace found",
                success=False,
                error=True,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        relation = get_object_or_404(
            DealContact,
            deal_id=deal_id,
            contact_id=contact_id,
            workspace=workspace,
            is_deleted=False,
        )
        relation.is_deleted = True
        relation.save(update_fields=["is_deleted"])

        return api_response(
            data=None,
            message="Contact unlinked from deal successfully",
            status_code=status.HTTP_200_OK,
        )


class CreateDealAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

    @extend_schema(
        request=CreateDealSerializer,
        responses={201: DealDetailSerializer},
        description="Create a new deal in the workspace",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request):
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

        serializer = CreateDealSerializer(
            data=request.data,
            context={
                "request": request,
                "workspace": workspace,
            },
        )

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Validation error",
                    "data": serializer.errors,
                    "success": False,
                    "error": "Invalid data",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                deal = serializer.save()
                response_serializer = DealDetailSerializer(
                    deal, context={"request": request}
                )

                return Response(
                    {
                        "message": "Deal created successfully",
                        "data": response_serializer.data,
                        "formatted_number": format_display_number(
                            "DEAL", deal.display_number
                        ),
                        "success": True,
                        "error": None,
                        "status_code": status.HTTP_201_CREATED,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception:
                transaction.set_rollback(True)
                return Response(
                    {
                        "message": "Deal creation failed",
                        "data": None,
                        "success": False,
                        "error": True,
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class PipelineWiseDealListAPIView(ListAPIView):
    serializer_class = DealPipelineSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, CanAssignDeal]
    pagination_class = None  # Add pagination if needed

    @extend_schema(
        responses={200: DealPipelineSerializer(many=True)},
        description="List deals grouped by pipeline stage",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="pipeline_stage",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            return Deal.objects.none()

        stage = self.request.query_params.get("pipeline_stage")
        queryset = Deal.objects.filter(workspace=workspace)

        if stage:
            queryset = queryset.filter(pipeline_stage__iexact=stage)

        return queryset

    @extend_schema(
        responses={200: DealPipelineSerializer(many=True)},
        description="List deals filtered by pipeline stage",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="pipeline_stage",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "message": "Deals fetched successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class DealRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, CanAssignDeal]
    queryset = Deal.objects.all()
    lookup_url_kwarg = "deal_id"

    def get_queryset(self):
        workspace = get_user_workspace(self.request.user)
        if not workspace:
            return Deal.objects.none()
        return Deal.objects.filter(workspace=workspace)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DealUpdateSerializer
        return DealDetailSerializer

    @extend_schema(
        responses={200: DealDetailSerializer},
        description="Retrieve a specific deal",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def retrieve(self, request, *args, **kwargs):
        deal = self.get_object()
        serializer = self.get_serializer(deal)

        return Response(
            {
                "message": "Deal details fetched successfully",
                "data": serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=DealUpdateSerializer,
        responses={200: DealDetailSerializer},
        description="Update a specific existing deal",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        deal = self.get_object()
        serializer = self.get_serializer(deal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = DealDetailSerializer(deal, context={"request": request})

        return Response(
            {
                "message": "Deal updated successfully",
                "data": response_serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={200: OpenApiResponse(description="Deal deleted successfully")},
        description="Soft delete a deal",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def destroy(self, request, *args, **kwargs):
        deal = self.get_object()
        deal.soft_delete()

        return Response(
            {
                "message": "Deal deleted successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": 200,
            },
            status=status.HTTP_200_OK,
        )


class DealRestoreAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, CanAssignDeal]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Deal restored successfully")},
        description="Restore a soft-deleted deal",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request, deal_id):
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

        deal = Deal.all_objects.filter(
            id=deal_id, workspace=workspace, is_deleted=True
        ).first()
        if not deal:
            return Response(
                {
                    "message": "Deal not found or not deleted",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = CanAssignDeal()
        if not permission.has_object_permission(request, self, deal):
            raise PermissionDenied("You do not have permission to restore this deal.")

        deal.restore()

        return Response(
            {
                "message": "Deal restored successfully",
                "data": None,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class DealAssignmentUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription,
        CanAssignDeal,
    ]

    @extend_schema(
        request=DealAssignmentSerializer,
        responses={200: DealDetailSerializer},
        description="Update deal assignment",
        tags=["Deals"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, deal_id):
        deal = get_object_or_404(Deal, id=deal_id)

        self.check_object_permissions(request, deal)

        serializer = DealAssignmentSerializer(
            deal,
            data=request.data,
            partial=True,
            context={"deal": deal},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Deal assignment updated successfully",
                "data": DealDetailSerializer(deal, context={"request": request}).data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class DealActivityFeedAPIView(ListAPIView):

    serializer_class = DealActivityFeedSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, DealAccessPermission]
    pagination_class = None  # Uses pagination from settings

    def get_queryset(self):
        user = self.request.user
        workspace = get_user_workspace(user)
        if not workspace:
            return DealActivity.objects.none()  # Return empty queryset if no workspace
        queryset = get_workspace_deal_activity_queryset(
            workspace=workspace,
            deal_id=self.kwargs.get("deal_id"),
            category=self.request.query_params.get("category"),
        )
        return queryset.order_by("-due_date")

    @extend_schema(
        responses={200: DealActivityFeedSerializer(many=True)},
        description="Get deal activity feed with filters",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
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


class CreateDealActivityAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, DealAccessPermission]

    @extend_schema(
        request=CreateDealActivitySerializer,
        responses={201: DealActivityFeedSerializer},
        description="Create a new deal activity",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request, deal_id):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_WORKSPACE",
                        "message": "No active workspace found",
                    },
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        deal = Deal.objects.filter(
            id=deal_id, workspace=workspace, is_deleted=False
        ).first()
        if not deal:
            return Response(
                {
                    "success": False,
                    "error": {"code": "DEAL_NOT_FOUND", "message": "Deal not found"},
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CreateDealActivitySerializer(
            data=request.data,
            context={"request": request, "workspace": workspace, "deal": deal},
        )
        if serializer.is_valid():
            activity = serializer.save(deal=deal)
            emit_crm_event(
                event_name="activity.created",
                workspace=workspace,
                payload={
                    "entity_id": activity.id,
                    "updated_fields": list(request.data.keys()) or ["activity_type"],
                },
                user=request.user,
            )
            response_serializer = DealActivityFeedSerializer(activity)
            return Response(
                {
                    "success": True,
                    "data": response_serializer.data,
                    "message": "Deal Activity created successfully",
                    "status_code": status.HTTP_201_CREATED,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid data",
                    "details": serializer.errors,
                },
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class DealActivityRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, DealAccessPermission]
    serializer_class = UpdateDealActivitySerializer

    def get_queryset(self):
        user = self.request.user
        workspace = get_user_workspace(user)
        if not workspace:
            return DealActivity.objects.none()
        deal_id = self.kwargs.get("deal_id")
        return get_workspace_deal_activity_queryset(
            workspace=workspace,
            deal_id=deal_id,
        )

    @extend_schema(
        responses={200: DealActivityFeedSerializer},
        description="Retrieve a specific deal activity",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DealActivityFeedSerializer(instance)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "Activity retrieved successfully",
                "status_code": status.HTTP_200_OK,
            }
        )

    @extend_schema(
        request=UpdateDealActivitySerializer,
        responses={200: DealActivityFeedSerializer},
        description="Update a specific deal activity",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={"workspace": instance.deal.workspace},
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = DealActivityFeedSerializer(instance)
        return Response(
            {
                "success": True,
                "data": response_serializer.data,
                "message": "Activity updated successfully",
                "status_code": status.HTTP_200_OK,
            }
        )

    @extend_schema(
        responses={204: OpenApiResponse(description="Activity deleted successfully")},
        description="Delete a specific deal activity",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "success": True,
                "message": "Activity deleted successfully",
                "status_code": status.HTTP_204_NO_CONTENT,
            },
            status=status.HTTP_204_NO_CONTENT,
        )


class LegacyDealListAPIView(APIView):
    """Deprecated compatibility endpoint. Use /api/deals/."""

    @extend_schema(
        operation_id="legacy_deals_list",
        responses={200: DealDetailSerializer(many=True)},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def get(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"get": "list"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/."
        return response

    @extend_schema(
        operation_id="legacy_deals_create",
        request=CreateDealSerializer,
        responses={201: DealDetailSerializer},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def post(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"post": "create"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/."
        return response


class LegacyDealDetailAPIView(APIView):
    """Deprecated compatibility endpoint. Use /api/deals/{id}/."""

    @extend_schema(
        operation_id="legacy_deals_detail_retrieve",
        responses={200: DealDetailSerializer},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def get(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"get": "retrieve"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/{id}/."
        return response

    @extend_schema(
        operation_id="legacy_deals_detail_patch",
        request=DealUpdateSerializer,
        responses={200: DealDetailSerializer},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def patch(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"patch": "partial_update"})(
            request, *args, **kwargs
        )
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/{id}/."
        return response

    @extend_schema(
        operation_id="legacy_deals_detail_put",
        request=DealUpdateSerializer,
        responses={200: DealDetailSerializer},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def put(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"patch": "partial_update"})(
            request, *args, **kwargs
        )
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/{id}/."
        return response

    @extend_schema(
        operation_id="legacy_deals_detail_delete",
        responses={200: OpenApiResponse(description="Deal deleted")},
        deprecated=True,
        tags=["Deals (Legacy)"],
        parameters=[workspace_header],
    )
    def delete(self, request, *args, **kwargs):
        response = DealViewSet.as_view({"delete": "destroy"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/deals/{id}/."
        return response


class RestoreDealActivityAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, DealAccessPermission]

    @extend_schema(
        request=None,
        responses={200: DealActivityFeedSerializer},
        description="Restore a deleted deal activity",
        tags=["Deal Activities"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request, deal_id, activity_id):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_WORKSPACE",
                        "message": "No active workspace found",
                    },
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            activity = DealActivity.all_objects.get(
                id=activity_id,
                deal_id=deal_id,
                deal__workspace=workspace,
                is_deleted=True,
            )
        except DealActivity.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ACTIVITY_NOT_FOUND",
                        "message": "Activity not found or not deleted",
                    },
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permission using DealAccessPermission
        permission = DealAccessPermission()
        if not permission.has_object_permission(request, self, activity.deal):
            raise PermissionDenied(
                "You do not have permission to restore this activity."
            )

        activity.restore()

        response_serializer = DealActivityFeedSerializer(activity)
        return Response(
            {
                "success": True,
                "data": response_serializer.data,
                "message": "Activity restored successfully",
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

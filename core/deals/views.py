from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Deal
from .serializers import (
    CreateDealSerializer,
    DealDetailSerializer,
    DealUpdateSerializer,
    DealPipelineSerializer,
    DealAssignmentSerializer,
)
from subscriptions.permissions import HasActiveSubscription
from .permissions import CanAssignDeal
from rest_framework.exceptions import PermissionDenied
from workspaces.utils import get_user_workspace
from django.shortcuts import get_object_or_404
from workspaces.permissions import IsWorkspaceMember
from common.utils import format_display_number


class CreateDealAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription, IsWorkspaceMember]

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

        deal = serializer.save()

        response_serializer = DealDetailSerializer(deal, context={"request": request})

        return Response(
            {
                "message": "Deal created successfully",
                "data": response_serializer.data,
                "formatted_number": format_display_number("DEAL", deal.display_number),
                "success": True,
                "error": None,
                "status_code": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


class PipelineWiseDealListAPIView(ListAPIView):
    serializer_class = DealPipelineSerializer
    permission_classes = [IsAuthenticated, HasActiveSubscription, CanAssignDeal]

    def get_queryset(self):
        stage = self.request.query_params.get("pipeline_stage")
        queryset = Deal.objects.all()  # only non-deleted deals

        if stage:
            queryset = queryset.filter(pipeline_stage__iexact=stage)

        return queryset

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

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DealUpdateSerializer
        return DealDetailSerializer

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

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        deal = self.get_object()
        serializer = self.get_serializer(deal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = DealDetailSerializer(deal, context={"request": request})

        return Response(
            {
                "message": "Detail updated successfully",
                "data": response_serializer.data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
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

    def post(self, request, deal_id):
        try:
            deal = Deal.all_objects.get(id=deal_id, is_deleted=True)
        except Deal.DoesNotExist:
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

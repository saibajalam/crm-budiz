from rest_framework import status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from .serializers import ContactSerializer
from contact.models import Contact
from drf_spectacular.utils import extend_schema, OpenApiResponse
from workspaces.permissions import IsWorkspaceMember
from common.api_response import api_response
from core.pagination import LeadPagination
from workspaces.utils import get_user_workspace
from common.eventing import emit_crm_event


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.none()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    pagination_class = LeadPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name", "email"]
    filterset_fields = ["created_by"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Contact.objects.none()

        if not getattr(self.request.user, "is_authenticated", False):
            return Contact.objects.none()

        workspace = getattr(self.request, "workspace", None) or get_user_workspace(
            self.request.user
        )
        if not workspace:
            return Contact.objects.none()

        return Contact.objects.filter(workspace=workspace, is_deleted=False)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
        },
        description="Create a new contact in the current workspace. The contact will be associated with the authenticated user as the creator.",
        tags=["Contacts"],
    )
    
    def perform_create(self, serializer):
        workspace = getattr(self.request, "workspace", None) or get_user_workspace(
            self.request.user
        )
        if not workspace:
            raise ValidationError({"detail": "No active workspace found"})

        serializer.save(workspace=workspace, created_by=self.request.user)

    @extend_schema(
        request=ContactSerializer,
        responses={201: ContactSerializer},
        description="Create a new contact in the current workspace.",
        tags=["Contacts"],
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_response(
            data=serializer.data,
            message="Contact created successfully",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
        },
        description="Retrieve a list of contacts in the current workspace.",
        tags=["Contacts"],
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data).data
            return api_response(
                data=paginated,
                message="Contacts fetched successfully",
                status_code=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            data=serializer.data,
            message="Contacts fetched successfully",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
        },
        description="Retrieve a specific contact in the current workspace.",
        tags=["Contacts"],
    )
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return api_response(
            data=serializer.data,
            message="Contact fetched successfully",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
        },
        description="Partially update a contact in the current workspace.",
        tags=["Contacts"],
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        emit_crm_event(
            event_name="contact.updated",
            workspace=instance.workspace,
            payload={
                "entity_id": instance.id,
                "updated_fields": list(request.data.keys()),
            },
            user=request.user,
        )
        return api_response(
            data=serializer.data,
            message="Contact updated successfully",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
        },
        description="Delete a contact in the current workspace.",
        tags=["Contacts"],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return api_response(
            data=None,
            message="Contact deleted successfully",
            status_code=status.HTTP_200_OK,
        )


class LegacyContactListAPIView(APIView):
    """Deprecated compatibility endpoint. Use /api/contacts/."""

    @extend_schema(
        operation_id="legacy_contacts_list",
        responses={200: ContactSerializer(many=True)},
        deprecated=True,
        tags=["Contacts (Legacy)"],
    )
    def get(self, request, *args, **kwargs):
        response = ContactViewSet.as_view({"get": "list"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/contacts/."
        return response

    @extend_schema(
        operation_id="legacy_contacts_create",
        request=ContactSerializer,
        responses={201: ContactSerializer},
        deprecated=True,
        tags=["Contacts (Legacy)"],
    )
    def post(self, request, *args, **kwargs):
        response = ContactViewSet.as_view({"post": "create"})(request, *args, **kwargs)
        response["X-Deprecated"] = "This endpoint is deprecated. Use /api/contacts/."
        return response


class LegacyContactDetailAPIView(APIView):
    """Deprecated compatibility endpoint. Use /api/contacts/{id}/."""

    @extend_schema(
        operation_id="legacy_contacts_detail_retrieve",
        responses={200: ContactSerializer},
        deprecated=True,
        tags=["Contacts (Legacy)"],
    )
    def get(self, request, *args, **kwargs):
        response = ContactViewSet.as_view({"get": "retrieve"})(request, *args, **kwargs)
        response["X-Deprecated"] = (
            "This endpoint is deprecated. Use /api/contacts/{id}/."
        )
        return response

    @extend_schema(
        operation_id="legacy_contacts_detail_update",
        request=ContactSerializer,
        responses={200: ContactSerializer},
        deprecated=True,
        tags=["Contacts (Legacy)"],
    )
    def patch(self, request, *args, **kwargs):
        response = ContactViewSet.as_view({"patch": "partial_update"})(
            request, *args, **kwargs
        )
        response["X-Deprecated"] = (
            "This endpoint is deprecated. Use /api/contacts/{id}/."
        )
        return response

    @extend_schema(
        operation_id="legacy_contacts_detail_delete",
        responses={200: OpenApiResponse(description="Contact deleted")},
        deprecated=True,
        tags=["Contacts (Legacy)"],
    )
    def delete(self, request, *args, **kwargs):
        response = ContactViewSet.as_view({"delete": "destroy"})(request, *args, **kwargs)
        response["X-Deprecated"] = (
            "This endpoint is deprecated. Use /api/contacts/{id}/."
        )
        return response

    
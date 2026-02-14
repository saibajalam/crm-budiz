from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse
from common.swagger import workspace_header
from django.conf import settings

from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace
from subscriptions.permissions import HasActiveSubscription

from ...models import Form
from ...api.v1.serailizers import (
    PublicFormSubmitSerializer,
    CreateFormSerializer,
    AddFieldSerializer,
    UpdateFormAssignmentSerializer,
)

# services
from ...services.submission_service import submit_public_form
from ...services.field_service import create_form_field
from ...services.assignment_service import update_form_assignment

import uuid


# =========================================================
# PUBLIC FORM SUBMIT
# =========================================================
class PublicFormSubmitThrottle(AnonRateThrottle):
    rate = "20/hour"


class PublicFormSubmitAPIView(APIView):
    permission_classes = []
    throttle_classes = [PublicFormSubmitThrottle]

    @extend_schema(
        operation_id="submit_public_form",
        request=PublicFormSubmitSerializer,
        responses={
            201: OpenApiResponse(description="Form submitted successfully"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Form not found or inactive"),
        },
        description="Submit a public form (no authentication required)",
        tags=["Forms"],
        auth=[],
    )
    def post(self, request, slug):
        form = get_object_or_404(Form, slug=slug, is_active=True)

        serializer = PublicFormSubmitSerializer(
            data=request.data,
            context={"form": form},
        )
        serializer.is_valid(raise_exception=True)

        submission = submit_public_form(
            form=form,
            data=serializer.validated_data["data"],
        )

        return Response(
            {
                "success": True,
                "message": "Form submitted successfully",
                "submission_id": submission.id,
                "status": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# CREATE FORM
# =========================================================
class CreateFormAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    @extend_schema(
        request=CreateFormSerializer,
        responses={201: CreateFormSerializer},
        description="Create a new form in workspace",
        tags=["Forms"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request):
        workspace = get_user_workspace(request.user)

        serializer = CreateFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = serializer.save(
            workspace=workspace,
            created_by=request.user,
            slug=str(uuid.uuid4())[:10],
        )

        response_serializer = CreateFormSerializer(form)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# =========================================================
# ADD FIELD
# =========================================================
class AddFieldAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    @extend_schema(
        request=AddFieldSerializer,
        responses={201: AddFieldSerializer},
        description="Add field to existing form",
        tags=["Forms"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request, form_id):
        workspace = get_user_workspace(request.user)

        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        serializer = AddFieldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        field = create_form_field(
            form=form,
            validated_data=serializer.validated_data,
        )

        return Response(AddFieldSerializer(field).data, status=201)


# =========================================================
# UPDATE ASSIGNMENT
# =========================================================
class UpdateFormAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    @extend_schema(
        request=UpdateFormAssignmentSerializer,
        responses={200: OpenApiResponse(description="Assignment updated successfully")},
        description="Update form assignment settings",
        tags=["Forms"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        serializer = UpdateFormAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_form_assignment(
            form=form,
            data=serializer.validated_data,
        )

        return Response({"success": True}, status=status.HTTP_200_OK)


# =========================================================
# EMBED
# =========================================================
class FormEmbedAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Form embed code retrieved")},
        description="Get embed code for form integration",
        tags=["Forms"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        api_base_url = getattr(settings, "API_BASE_URL", "https://api.yourcrm.com")

        embed_code = f"""
<script>
fetch("{api_base_url}/public/forms/{form.slug}/submit/", {{
 method: "POST",
 headers: {{ "Content-Type": "application/json" }},
 body: JSON.stringify({{
   data: {{
     "Full Name": "",
     "Email": "",
     "Phone": ""
   }}
 }})
}});
</script>
"""

        return Response({"embed_code": embed_code})

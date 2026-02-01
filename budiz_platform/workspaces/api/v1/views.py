from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from subscriptions.permissions import HasActiveSubscription
from ...models import Workspace, WorkspaceMember, WorkspaceInvite
from .serializers import (
    WorkspaceCreateSerializer,
    WorkspaceEmailInviteSerializer,
    WorkspaceMemberRoleUpdateSerializer,
)
from ...permissions import CanInviteToWorkspace, IsWorkspaceOwner
from ...utils import send_workspace_invite_email
from django.shortcuts import get_object_or_404


class WorkspaceCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        serializer = WorkspaceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = serializer.save(owner=request.user)

        return Response(
            {
                "message": "Workspace created successfully",
                "data": WorkspaceCreateSerializer(workspace).data,
                "success": True,
                "error": None,
                "status_code": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


class WorkspaceEmailInviteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        CanInviteToWorkspace,
        HasActiveSubscription,
    ]

    def post(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response(
                {
                    "message": "Workspace not found",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorkspaceEmailInviteSerializer(
            data=request.data,
            context={"workspace": workspace, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        invite = serializer.save()

        send_workspace_invite_email(invite)

        return Response(
            {
                "message": "Workspace invitation sent successfully",
                "data": {"email": invite.email, "role": invite.role},
                "success": True,
                "error": None,
                "status_code": 201,
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptWorkspaceInviteAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request, token):
        try:
            invite = WorkspaceInvite.objects.get(token=token, is_accepted=False)
        except WorkspaceInvite.DoesNotExist:
            return Response(
                {
                    "message": "Invalid or expired invite",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Email must match logged-in user
        if request.user.email != invite.email:
            return Response(
                {
                    "message": "This invite does not belong to your email",
                    "data": None,
                    "success": False,
                    "error": True,
                    "status_code": 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create membership
        WorkspaceMember.objects.create(
            workspace=invite.workspace,
            user=request.user,
            role=invite.role,
        )

        invite.mark_accepted()

        return Response(
            {
                "message": "Workspace invitation accepted successfully",
                "data": {
                    "workspace_id": invite.workspace.id,
                    "role": invite.role,
                },
                "success": True,
                "error": None,
                "status_code": 200,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceInviteResendAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request, invite_id):
        invite = get_object_or_404(
            WorkspaceInvite, id=invite_id, workspace_owner=request.user
        )

        if invite.is_accepted:
            return Response(
                {
                    "detail": "Invite already accepted.",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_404_Bad_Request,
            )

        invite.resend()

        send_workspace_invite_email(
            email=invite.email, token=invite.token, workspace=invite.workspace
        )

        return Response(
            {
                "success": True,
                "data": "Invite resend successfully.",
                "error": None,
                "status": status.HTTP_200_OK,
            }
        )


class WorkspaceMemberRoleUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceOwner]

    def get_workspace(self):
        return get_object_or_404(Workspace, id=self.kwargs["workspace_id"])

    def patch(self, request, workspace_id, member_id):
        workspace = self.get_workspace()

        member = get_object_or_404(WorkspaceMember, id=member_id, workspace=workspace)

        # Prevent owner modification
        if member.role == "owner":
            return Response(
                {"detail": "Owner role cannot be changed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WorkspaceMemberRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member.role = serializer.validated_data["role"]
        member.save(update_fields=["role"])

        return Response(
            {
                "success": True,
                "detail": "Member role updated successfully",
                "error": None,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )

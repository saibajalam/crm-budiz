from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import WorkspaceMember


class IsWorkspaceOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id")
        if not workspace_id:
            return False

        return WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            role__in=["owner", "admin"],
        ).exists()


class IsValidWorkspaceHeader(BasePermission):
    message = "Workspace header validation failed."

    def has_permission(self, request, view):
        workspace_id = request.headers.get("X-Workspace-ID") or request.META.get(
            "HTTP_X_WORKSPACE_ID"
        )

        if not workspace_id:
            raise ValidationError({"detail": "Workspace header is required."})

        try:
            workspace_id = int(workspace_id)
        except (TypeError, ValueError):
            raise ValidationError({"detail": "Workspace header is required."})

        is_member = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            is_active=True,
        ).exists()

        if not is_member:
            raise PermissionDenied({"detail": "Please enter your own workspace_id."})

        request.workspace_id = workspace_id
        setattr(request.user, "_current_workspace_id", workspace_id)
        return True


class IsWorkspaceOwner(BasePermission):
    def has_permission(self, request, view):
        workspace = view.get_workspace()
        return workspace.owner == request.user


class IsWorkspaceMember(IsValidWorkspaceHeader):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return obj.workspace.members.filter(user=request.user).exists()


class CanInviteToWorkspace(BasePermission):
    def has_permission(self, request, view):
        workspace_id = request.data.get("workspace_id") or view.kwargs.get(
            "workspace_id"
        )

        if not workspace_id:
            return False

        return WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            role__in=["owner", "admin"],
            is_active=True,
        ).exists()

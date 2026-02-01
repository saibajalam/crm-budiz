from rest_framework.permissions import BasePermission
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



class IsWorkspaceOwner(BasePermission):
    def has_permission(self, request, view):
        workspace = view.get_workspace()
        return workspace.owner == request.user
    

class IsWorkspaceMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.workspace.members.filter(user=request.user).exists()
    

class CanInviteToWorkspace(BasePermission):
    def has_permission(self, request, view):
        workspace_id = (
            request.data.get("workspace_id")
            or view.kwargs.get("workspace_id")
        )

        if not workspace_id:
            return False

        return WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            role__in=["owner", "admin"],
            is_active=True,
        ).exists()
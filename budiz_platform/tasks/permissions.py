from rest_framework.permissions import BasePermission
from workspaces.models import WorkspaceMember


class TaskAccessPermission(BasePermission):
    """
    Allow access to tasks if the user is an active member of any workspace
    and to objects only within their workspace.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return WorkspaceMember.objects.filter(user=user, is_active=True).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return WorkspaceMember.objects.filter(
            workspace=obj.workspace,
            user=user,
            is_active=True,
        ).exists()


class TaskManagePermission(BasePermission):
    """
    Allow updates/deletes if user is:
    - Workspace owner/admin/manager
    - Task creator
    - Task assignee
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if obj.created_by_id == user.id or obj.assigned_to_id == user.id:
            return True

        return WorkspaceMember.objects.filter(
            workspace=obj.workspace,
            user=user,
            role__in=["owner", "admin", "manager"],
            is_active=True,
        ).exists()

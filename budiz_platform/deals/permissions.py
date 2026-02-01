from rest_framework.permissions import BasePermission
from workspaces.models import WorkspaceMember


class DealAccessPermission(BasePermission):
    """
    Allow access to deals if the user is a member of the workspace.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Check if user is a member of any workspace
        return WorkspaceMember.objects.filter(
            user=user,
            is_active=True,
        ).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Handle both Deal and DealActivity objects
        if hasattr(obj, "deal"):  # DealActivity object
            workspace = obj.deal.workspace
        else:  # Deal object
            workspace = obj.workspace

        # Check if user is a member of the workspace
        return WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True,
        ).exists()


class CanAssignDeal(BasePermission):
    """
    Allow deal assignment only if:
    - Workspace owner or admin
    - Deal creator
    """

    def has_object_permission(self, request, view, deal):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Workspace-level role check
        if WorkspaceMember.objects.filter(
            workspace=deal.workspace,
            user=user,
            role__in=["owner", "admin"],
            is_active=True,
        ).exists():
            return True

        # Deal creator (still must be in same workspace implicitly)
        return deal.created_by_id == user.id

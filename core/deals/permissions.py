from rest_framework.permissions import BasePermission
from workspaces.models import WorkspaceMember


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

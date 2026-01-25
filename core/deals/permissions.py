from rest_framework.permissions import BasePermission


class IsDealOwnerAssigneeOrAdmin(BasePermission):
    """
    Allow only:
    - Deal creator
    - Assigned user
    - Admin / SuperAdmin / Manager
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Role-based access
        if user.is_admin_or_manager:
            return True

        # Deal creator
        if obj.created_by_id == user.id:
            return True

        # Assigned user
        if obj.assigned_to_id == user.id:
            return True

        return False

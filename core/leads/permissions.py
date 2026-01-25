from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class CanDeleteLead(BasePermission):
    """
    Allow delete only if:
    - user is lead owner
    -user is superadmin
    - user has admin role
    - user has manager role
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # 1️⃣ Lead owner can delete
        if obj.created_by == user:
            return True

        # 2️⃣ SuperAdmin, Admin or Manager role can delete
        if user.is_admin_or_manager:
            return True


class CanDeleteLeadActivity(BasePermission):
    """
    Permission to only allow:
    - creator of the activity
    - admin
    - superadmin
    to delete a LeadActivity.
    """

    def has_object_permission(self, request, view, obj):
        # If no user, deny
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow superuser
        if request.user.is_superuser:
            return True

        # You can also allow based on role if your User model has roles
        if request.user.is_admin_or_manager:
            return True

        # Allow the user who created the activity
        if obj.performed_by == request.user:
            return True

        # Otherwise deny
        return False

from rest_framework.permissions import BasePermission


# =========================================================
# Helpers
# =========================================================


def get_workspace(request):
    return getattr(request, "workspace", None)


def get_member(request):
    """
    Returns WorkspaceMember object or None
    """
    workspace = get_workspace(request)
    if not workspace:
        return None

    return (
        workspace.members.filter(user=request.user, is_active=True)
        .select_related("role")
        .first()
    )


def get_role_name(request):
    """
    Returns role name in lowercase
    """
    # SUPERADMIN BYPASS (global)
    if request.user and request.user.is_authenticated:
        if getattr(request.user, "is_superuser", False):
            return "superadmin"

    member = get_member(request)
    if not member or not member.role:
        return None

    return member.role.name.lower()


def is_superadmin(request):
    role = get_role_name(request)
    return role == "superadmin"


# =========================================================
# Base Permission
# =========================================================


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsWorkspaceMember(BasePermission):
    """
    Requires user to belong to workspace
    SuperAdmin bypasses
    """

    def has_permission(self, request, view):
        if is_superadmin(request):
            return True

        member = get_member(request)
        return member is not None


# =========================================================
# ROLE PERMISSIONS
# =========================================================


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_superadmin(request)


class IsAdmin(BasePermission):
    """
    Admin + SuperAdmin
    """

    def has_permission(self, request, view):
        role = get_role_name(request)
        return role in ["superadmin", "admin"]


class IsManager(BasePermission):
    """
    Manager + Admin + SuperAdmin
    """

    def has_permission(self, request, view):
        role = get_role_name(request)
        return role in ["superadmin", "admin", "manager"]


class IsSales(BasePermission):
    """
    Sales + Manager + Admin + SuperAdmin
    """

    def has_permission(self, request, view):
        role = get_role_name(request)
        return role in [
            "superadmin",
            "admin",
            "manager",
            "sales_representative",
        ]


# =========================================================
# Generic Role Permission
# =========================================================


class RolePermission(BasePermission):
    """
    Use in views like:

    class MyView(APIView):
        permission_classes = [RolePermission]
        required_roles = ["admin", "manager"]
    """

    required_roles = []

    def has_permission(self, request, view):
        role = get_role_name(request)

        if role == "superadmin":
            return True

        return role in self.required_roles


# =========================================================
# OBJECT LEVEL PERMISSIONS
# =========================================================


class CanAssignDeal(BasePermission):
    """
    Owner/admin/manager OR creator can assign
    SuperAdmin bypass
    """

    def has_object_permission(self, request, view, obj):
        role = get_role_name(request)

        if role in ["superadmin", "admin", "manager"]:
            return True

        return obj.created_by == request.user


class IsOwnerOrAdminOrSelf(BasePermission):
    """
    Used for profile/user updates
    """

    def has_object_permission(self, request, view, obj):
        role = get_role_name(request)

        if role in ["superadmin", "admin"]:
            return True

        return obj == request.user


class SameWorkspaceOnly(BasePermission):
    """
    Prevent cross-workspace access
    SuperAdmin bypass
    """

    def has_object_permission(self, request, view, obj):
        if is_superadmin(request):
            return True

        workspace = get_workspace(request)
        return getattr(obj, "workspace_id", None) == workspace.id

from workspaces.models import Workspace, WorkspaceMember
from workspaces.utils import get_user_workspace


def get_workspace_for_user(user):
    workspace = get_user_workspace(user)
    if workspace:
        return workspace

    return Workspace.objects.filter(owner=user, is_active=True).first()


def get_workspace_from_request(request):
    workspace_id = request.headers.get("X-Workspace-ID")
    if not workspace_id:
        return None

    try:
        workspace_id = int(workspace_id)
    except (TypeError, ValueError):
        return None

    workspace = Workspace.objects.filter(id=workspace_id, is_active=True).first()
    if not workspace:
        return None

    if workspace.owner_id == request.user.id:
        return workspace

    is_member = WorkspaceMember.objects.filter(
        workspace_id=workspace_id,
        user=request.user,
        is_active=True,
    ).exists()

    return workspace if is_member else None


def is_workspace_active(workspace):
    if not workspace or not workspace.is_active:
        return False

    subscription = getattr(workspace, "subscription", None)
    if not subscription:
        return False

    return subscription.is_valid()


def is_user_active(user):
    subscription = getattr(user, "subscription", None)
    if not subscription:
        return False

    return subscription.is_valid()


def has_active_subscription(user):
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "is_superuser", False):
        return True

    if getattr(user, "has_role", None):
        try:
            if user.has_role("superadmin"):
                return True
        except Exception:
            pass

    workspace = get_workspace_for_user(user)
    if workspace:
        return is_workspace_active(workspace)

    if user.is_trial_active():
        return True

    return is_user_active(user)


def has_active_subscription_for_request(request):
    user = request.user
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "is_superuser", False):
        return True

    if getattr(user, "has_role", None):
        try:
            if user.has_role("superadmin"):
                return True
        except Exception:
            pass

    workspace = get_workspace_from_request(request) or get_workspace_for_user(user)
    if workspace:
        return is_workspace_active(workspace)

    if user.is_trial_active():
        return True

    return is_user_active(user)

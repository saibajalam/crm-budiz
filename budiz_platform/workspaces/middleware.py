from django.http import JsonResponse

from workspaces.models import WorkspaceMember


class WorkspaceContextMiddleware:
    """Attach request.workspace for authenticated API requests and enforce membership."""

    EXEMPT_PREFIXES = (
        "/api/login/",
        "/api/register/",
        "/api/token/",
        "/api/schema/",
        "/api/docs/",
        "/api/redoc/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if request.path.startswith(self.EXEMPT_PREFIXES):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        workspace_id = request.headers.get("X-Workspace-ID") or request.META.get(
            "HTTP_X_WORKSPACE_ID"
        )
        if not workspace_id:
            return JsonResponse(
                {
                    "success": False,
                    "data": None,
                    "message": "Workspace header is required",
                    "error": True,
                },
                status=400,
            )

        membership = (
            WorkspaceMember.objects.select_related("workspace")
            .filter(
                workspace_id=workspace_id,
                user=user,
                is_active=True,
            )
            .first()
        )
        if not membership:
            return JsonResponse(
                {
                    "success": False,
                    "data": None,
                    "message": "User is not a member of this workspace",
                    "error": True,
                },
                status=403,
            )

        request.workspace = membership.workspace
        request.workspace_id = membership.workspace_id
        setattr(user, "_current_workspace_id", membership.workspace_id)

        return self.get_response(request)

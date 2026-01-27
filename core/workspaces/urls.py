from django.urls import path
from .views import (
    WorkspaceCreateAPIView,
    WorkspaceEmailInviteAPIView,
    AcceptWorkspaceInviteAPIView,
    WorkspaceInviteResendAPIView,
    WorkspaceMemberRoleUpdateAPIView,
)

urlpatterns = [
    path("workspaces/", WorkspaceCreateAPIView.as_view(), name="create_workspace"),
    path(
        "workspaces/<int:workspace_id>/invite-email/",
        WorkspaceEmailInviteAPIView.as_view(),
        name="workspace_email_invite",
    ),
    path(
        "workspaces/invite/accept/<uuid:token>/",
        AcceptWorkspaceInviteAPIView.as_view(),
        name="accept_workspace_invite",
    ),
    path(
        "workspaces/<int:invite_id>/resend/",
        WorkspaceInviteResendAPIView.as_view(),
        name="workspace-invite-resend",
    ),
    path(
        "workspaces/<int:workspace_id>/members/<int:member_id>/role/",
        WorkspaceMemberRoleUpdateAPIView.as_view(),
        name="workspace-member-role-update",
    ),
]

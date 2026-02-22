from django.core.mail import send_mail
from django.conf import settings


def send_workspace_invite_email(invite):

    frontend_url = getattr(settings, "FRONTEND_URL", None)

    if not frontend_url:
        raise Exception("FRONTEND_URL is not configured")

    invite_link = f"{settings.FRONTEND_URL}/accept-invite/{invite.token}"

    subject = "You're invited to join a workspace"
    message = f"""
You have been invited to join the workspace "{invite.workspace.name}".

Role: {invite.role}

Click the link below to accept the invitation:
{invite_link}

If you didn’t request this, you can ignore this email.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [invite.email],
        fail_silently=False,
    )

def _resolve_workspace_id_from_user(user):
    workspace_id = getattr(user, "_current_workspace_id", None)
    if workspace_id is None:
        return None

    try:
        return int(workspace_id)
    except (TypeError, ValueError):
        return None


def get_user_workspace(user):
    workspace_id = _resolve_workspace_id_from_user(user)

    memberships = user.workspace_members.filter(is_active=True).select_related("workspace")

    if workspace_id is not None:
        membership = memberships.filter(workspace_id=workspace_id).first()
        return membership.workspace if membership else None

    membership = memberships.first()
    return membership.workspace if membership else None
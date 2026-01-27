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



def get_user_workspace(user):
    membership = (
        user.workspace_members
        .filter(is_active=True)
        .select_related("workspace")
        .first()
    )

    return membership.workspace if membership else None

from django.core.mail import send_mail
from django.conf import settings


def send_verification_email(user, token):
    verification_link = f"http://localhost:8000/api/verify-email/?token={token.token}"

    send_mail(
        subject="Verify your email",
        message=f"Click the link to verify your email: {verification_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

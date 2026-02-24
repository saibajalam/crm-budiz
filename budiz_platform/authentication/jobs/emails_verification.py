from authentication.models import EmailVerificationToken
from authentication.utils import send_verification_email
from django.core.exceptions import ValidationError


def resend_email_verification(user):
    if user.is_email_verified:
        raise ValidationError("Email already verified")

    existing_token = EmailVerificationToken.objects.filter(
        user=user, is_used=False
    ).first()

    if existing_token and not existing_token.is_expired():
        token = existing_token
    else:
        EmailVerificationToken.objects.filter(user=user, is_used=False).update(
            is_used=True
        )

        token = EmailVerificationToken.objects.create(user=user)

    send_verification_email(user, token)
    return token

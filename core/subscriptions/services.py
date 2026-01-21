from datetime import timedelta
from django.utils import timezone
from .models import CompanySubscription, UserSubscription


def activate_subscription(company, plan):
    
    CompanySubscription.objects.filter(
        company=company,
        is_active=True
    ).update(is_active=False)

    subscription = CompanySubscription.objects.create(
        company=company,
        plan=plan,
        started_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=plan.duration_days),
        is_active=True
    )

    return subscription


def activate_user_subscription(user, plan):
    # Deactivate existing subscription
    UserSubscription.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False)

    # Create new subscription
    subscription = UserSubscription.objects.create(
        user=user,
        plan=plan,
        started_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=plan.duration_days),
        is_active=True
    )

    return subscription
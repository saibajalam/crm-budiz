from datetime import timedelta
from django.utils import timezone
from subscriptions.models import (
    SubscriptionStatus,
    UserSubscription,
    WorkspaceSubscription,
)


def activate_workspace_subscription(workspace, plan):
    WorkspaceSubscription.objects.filter(
        workspace=workspace,
        status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
    ).update(status=SubscriptionStatus.CANCELLED, expires_at=timezone.now())

    subscription = WorkspaceSubscription.objects.create(
        workspace=workspace,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        started_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=plan.duration_days),
    )

    return subscription


def activate_user_subscription(user, plan):
    UserSubscription.objects.filter(
        user=user,
        status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
    ).update(status=SubscriptionStatus.CANCELLED, expires_at=timezone.now())

    subscription = UserSubscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        started_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=plan.duration_days),
    )

    return subscription

from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import SubscriptionStatus, WorkspaceSubscription


class Command(BaseCommand):
    help = "Expire subscriptions whose end date has passed"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        expired = WorkspaceSubscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
            expires_at__lt=now,
        )

        count = expired.count()

        expired.update(status=SubscriptionStatus.EXPIRED)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} workspace subscriptions expired"
            )
        )

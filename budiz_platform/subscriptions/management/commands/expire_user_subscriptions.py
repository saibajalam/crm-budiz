from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import SubscriptionStatus, UserSubscription


class Command(BaseCommand):
    help = "Expire individual user subscriptions"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        expired = UserSubscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
            expires_at__lt=now,
        )

        count = expired.count()
        expired.update(status=SubscriptionStatus.EXPIRED)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} user subscriptions expired"
            )
        )

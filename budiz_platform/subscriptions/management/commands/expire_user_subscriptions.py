from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import UserSubscription


class Command(BaseCommand):
    help = "Expire individual user subscriptions"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        expired = UserSubscription.objects.filter(
            is_active=True,
            ends_at__lt=now
        )

        count = expired.count()
        expired.update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} user subscriptions expired"
            )
        )

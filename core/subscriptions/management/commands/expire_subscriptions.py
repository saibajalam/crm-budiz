from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import CompanySubscription


class Command(BaseCommand):
    help = "Expire subscriptions whose end date has passed"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        expired = CompanySubscription.objects.filter(
            is_active=True,
            ends_at__lt=now
        )

        count = expired.count()

        expired.update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} company subscriptions expired"
            )
        )

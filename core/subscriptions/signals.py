from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Company


@receiver(post_save, sender=Company)
def start_company_trial(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.trial_ends_at:
        return

    now = timezone.now()

    instance.trial_starts_at = now
    instance.trial_ends_at = now + timedelta(days=settings.TRIAL_PERIOD_DAYS)
    instance.save(update_fields=["trial_starts_at", "trial_ends_at"])

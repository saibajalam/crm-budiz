from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum, Count, Q

from deals.models import Deal
from leads.models import Lead
from .models import DealAnalytics, UserAnalytics


@receiver(post_save, sender=Lead)
def update_lead_conversion_analytics(sender, instance, created, **kwargs):
    """
    Update analytics when a lead is converted.
    This signal triggers when a lead's status changes to 'converted'.
    """
    if instance.status == "converted" and instance.is_converted:
        # Update DealAnalytics for the workspace
        today = timezone.now().date()
        analytics, created = DealAnalytics.objects.get_or_create(
            workspace=instance.workspace,
            date=today,
            defaults={"leads_converted": 0, "total_leads_qualified": 0},
        )

        # Increment leads converted count
        analytics.leads_converted += 1

        # Calculate conversion rate
        # Get total qualified leads for this workspace
        qualified_leads = Lead.objects.filter(
            workspace=instance.workspace, status__in=["qualified", "converted"]
        ).count()

        analytics.total_leads_qualified = qualified_leads

        if qualified_leads > 0:
            converted_count = Lead.objects.filter(
                workspace=instance.workspace, status="converted"
            ).count()
            analytics.conversion_rate = (converted_count / qualified_leads) * 100

        analytics.save()

        # Update UserAnalytics for the user who converted the lead
        # (Assuming the user who triggered the conversion is the one who should get credit)
        # Note: This might need adjustment based on your business logic
        user_analytics, created = UserAnalytics.objects.get_or_create(
            user=instance.created_by,
            workspace=instance.workspace,
            date=today,
            defaults={"leads_converted": 0, "conversion_value": 0.00},
        )

        user_analytics.leads_converted += 1
        user_analytics.save()


@receiver(post_save, sender=Deal)
def update_deal_creation_analytics(sender, instance, created, **kwargs):
    """
    Update analytics when a deal is created, especially for converted deals.
    """
    if created:
        today = timezone.now().date()

        # Update DealAnalytics
        analytics, created = DealAnalytics.objects.get_or_create(
            workspace=instance.workspace,
            date=today,
            defaults={"total_deals": 0, "total_value": 0.00},
        )

        analytics.total_deals += 1
        analytics.total_value += instance.value
        analytics.pipeline_value += instance.value
        analytics.save()

        # Update UserAnalytics
        user_analytics, created = UserAnalytics.objects.get_or_create(
            user=instance.created_by,
            workspace=instance.workspace,
            date=today,
            defaults={"deals_created": 0},
        )

        user_analytics.deals_created += 1

        # If this deal was created from a lead conversion, update conversion value
        if instance.created_from_lead:
            user_analytics.conversion_value += instance.value

        user_analytics.save()

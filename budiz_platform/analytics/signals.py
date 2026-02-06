from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Sum, Q

from deals.models import Deal
from leads.models import Lead
from .models import DealAnalytics, UserAnalytics
from analytics.cache import invalidate_workspace_cache


def get_today():
    return timezone.now().date()


def update_deal_analytics(workspace, date):
    """
    Batch update DealAnalytics for a workspace on a specific date.
    """
    # Total qualified leads
    total_qualified = Lead.objects.filter(
        workspace=workspace, status__in=["qualified", "converted"]
    ).count()

    # Total converted leads
    converted_count = Lead.objects.filter(
        workspace=workspace, status="converted"
    ).count()

    # Total deals and values today
    deals_today = Deal.objects.filter(workspace=workspace, created_at__date=date)

    total_deals = deals_today.count()
    total_value = deals_today.aggregate(sum=Sum("value"))["sum"] or 0
    pipeline_value = deals_today.aggregate(sum=Sum("value"))["sum"] or 0

    analytics, _ = DealAnalytics.objects.get_or_create(
        workspace=workspace,
        date=date,
        defaults={
            "leads_converted": converted_count,
            "total_leads_qualified": total_qualified,
            "conversion_rate": (
                (converted_count / total_qualified * 100) if total_qualified else 0
            ),
            "total_deals": total_deals,
            "total_value": total_value,
            "pipeline_value": pipeline_value,
        },
    )

    # Update if exists
    analytics.leads_converted = converted_count
    analytics.total_leads_qualified = total_qualified
    analytics.conversion_rate = (
        (converted_count / total_qualified * 100) if total_qualified else 0
    )
    analytics.total_deals = total_deals
    analytics.total_value = total_value
    analytics.pipeline_value = pipeline_value
    analytics.save()


def update_user_analytics(user, workspace, date):
    """
    Batch update UserAnalytics for a user on a specific date.
    """
    leads_converted = Lead.objects.filter(
        workspace=workspace, created_by=user, status="converted"
    ).count()

    conversion_value = (
        Deal.objects.filter(
            workspace=workspace,
            created_by=user,
            created_from_lead__isnull=False,
            created_at__date=date,
        ).aggregate(sum=Sum("value"))["sum"]
        or 0
    )

    deals_created = Deal.objects.filter(
        workspace=workspace, created_by=user, created_at__date=date
    ).count()

    user_analytics, _ = UserAnalytics.objects.get_or_create(
        user=user,
        workspace=workspace,
        date=date,
        defaults={
            "leads_converted": leads_converted,
            "conversion_value": conversion_value,
            "deals_created": deals_created,
        },
    )

    user_analytics.leads_converted = leads_converted
    user_analytics.conversion_value = conversion_value
    user_analytics.deals_created = deals_created
    user_analytics.save()


@receiver(post_save, sender=Lead)
def lead_conversion_handler(sender, instance, **kwargs):
    """
    Signal for Lead conversion, batch updates analytics per workspace/date.
    """
    if instance.status != "converted" or not instance.is_converted:
        return

    workspace = instance.workspace
    today = get_today()

    # Update workspace analytics
    update_deal_analytics(workspace, today)

    # Update user analytics
    if instance.created_by:
        update_user_analytics(instance.created_by, workspace, today)

    # Invalidate dashboard cache
    invalidate_workspace_cache(workspace.id)


@receiver(post_save, sender=Deal)
def deal_creation_handler(sender, instance, created, **kwargs):
    """
    Signal for Deal creation, batch updates analytics per workspace/date.
    """
    if not created:
        return

    workspace = instance.workspace
    today = get_today()

    # Update workspace analytics
    update_deal_analytics(workspace, today)

    # Update user analytics
    if instance.created_by:
        update_user_analytics(instance.created_by, workspace, today)

    # Invalidate dashboard cache
    invalidate_workspace_cache(workspace.id)

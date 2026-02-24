from django.db import models

# Create your models here.


class DealAnalytics(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="deal_analytics"
    )
    date = models.DateField(auto_now_add=True)
    total_deals = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    won_deals = models.IntegerField(default=0)
    won_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    lost_deals = models.IntegerField(default=0)
    pipeline_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Lead conversion metrics
    leads_converted = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # Percentage
    total_leads_qualified = models.IntegerField(default=0)

    class Meta:
        db_table = "deal_analytics"
        unique_together = ("workspace", "date")


class UserAnalytics(models.Model):
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="analytics",
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="user_analytics"
    )
    date = models.DateField()
    deals_created = models.IntegerField(default=0)
    deals_closed = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    activities_completed = models.IntegerField(default=0)

    # Lead conversion metrics
    leads_converted = models.IntegerField(default=0)
    conversion_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

    class Meta:
        db_table = "user_analytics"
        unique_together = ("user", "date")
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["workspace", "date"]),
        ]


class AutomationAnalytics(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="automation_analytics",
    )
    date = models.DateField()

    total_executions = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    leads_created_via_automation = models.IntegerField(default=0)
    deals_won_via_automation = models.IntegerField(default=0)

    class Meta:
        db_table = "automation_analytics"
        unique_together = ("workspace", "date")

from django.db import models
from django.utils import timezone
from datetime import timedelta
from common.models import TimeStampedModel
from django.conf import settings

# Create your models here.

User = settings.AUTH_USER_MODEL

class Company(TimeStampedModel):
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField(unique=True) 
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owned_company"
    )

    trial_started_at = models.DateTimeField(auto_now_add=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "Company"

    def save(self, *args, **kwargs):
        if not self.pk and not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)

    def is_trial_active(self):
        return self.trial_ends_at and self.trial_ends_at > timezone.now()
    

    def get_active_subscription(self):
        return self.subscriptions.filter(is_active=True).first()

    def has_active_subscription(self):
        subscription = self.get_active_subscription()
        return subscription and subscription.is_valid()

    def __str__(self):
        return self.company_name
    

class SubscriptionPlan(TimeStampedModel):
    plan_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Public plan identifier (e.g. BASIC_30, PRO_90)"
    )
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField() 

    class Meta:
        db_table = "subscription_plan"
    
    def __str__(self):
        return f"{self.name} ({self.plan_id})"



class UserSubscription(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subscriptions",
        on_delete=models.CASCADE
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)

    reminder_sent_days = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "user_subscription"

    def is_valid(self):
        return self.is_active and self.ends_at >= timezone.now()



class CompanySubscription(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)

    reminder_sent_days = models.JSONField(default=list, blank=True)

    def is_valid(self):
        return self.is_active and self.ends_at > timezone.now()
    
    class Meta:
        db_table = "company_subscription"
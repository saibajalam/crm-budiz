from django.db import models
from common.models import TimeStampedModel
from django.conf import settings
from django.utils import timezone
from common.managers import SoftDeleteManager
from common.mixins import SoftDeleteModel

# Create your models here.

User = settings.AUTH_USER_MODEL


class Deal(TimeStampedModel, SoftDeleteModel):
    PIPELINE_CHOICES = (
        ("lead", "Lead"),
        ("contact_made", "Contact Made"),
        ("proposal_sent", "Proposal Sent"),
        ("negotiation", "Negotiation"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    )

    title = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    probability = models.PositiveIntegerField(help_text="Probability in percentage")

    pipeline_stage = models.CharField(
        max_length=20, choices=PIPELINE_CHOICES, default="lead"
    )

    expected_close_date = models.DateField(null=True, blank=True)
    display_number = models.PositiveIntegerField()
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_deals",
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="deals",
    )

    notes = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_deals"
    )

    objects = SoftDeleteManager()  # default
    all_objects = models.Manager()  # includes deleted deals

    class Meta:
        db_table = "deals"
        unique_together = ("workspace", "display_number")

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class DealActivity(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=225)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ],
        default="pending",
    )
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ("call", "Call"),
            ("meeting", "Meeting"),
            ("email", "Email"),
            ("other", "Other"),
        ],
    )
    assigned_to = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="activities",
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="deal_activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

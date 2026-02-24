from django.db import models
from authentication.models import TimeStampedModel
from core.constants import LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES
from django.conf import settings
from common.managers import SoftDeleteManager
from django.utils import timezone
from common.mixins import SoftDeleteModel
from core.constants import ACTIVITY_TYPES, PRIORITY_CHOICES
import PIL

# Create your models here.


class Lead(TimeStampedModel, SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, unique=True)

    company = models.CharField(max_length=150, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to="leads/images/", null=True, blank=True)
    document = models.FileField(upload_to="leads/documents/", null=True, blank=True)
    display_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default="NEW")

    source = models.CharField(
        max_length=30, choices=LEAD_SOURCE_CHOICES, default="WEBSITE"
    )

    score = models.PositiveIntegerField(default=0)
    is_converted = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leads"
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="leads",
    )

    objects = SoftDeleteManager()  # default
    all_objects = models.Manager()  # includes deleted leads

    class Meta:
        indexes = [
            models.Index(fields=["first_name", "last_name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_converted"]),
            models.Index(fields=["workspace", "created_at"]),
            models.Index(fields=["status", "source"]),
            models.Index(fields=["workspace", "is_converted"]),
            models.Index(fields=["workspace", "status"]),
        ]
        db_table = "leads"
        unique_together = ("workspace", "display_number")

    def soft_delete(self):
        super().soft_delete()

        # Cascade to Lead Activities
        self.activities.all().update(is_deleted=True, deleted_at=timezone.now())

        # Cascade to Deals
        self.deals.all().update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        super().restore()
        self.activities.all().update(is_deleted=False, deleted_at=None)
        self.deals.all().update(is_deleted=False, deleted_at=None)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class LeadActivity(TimeStampedModel, SoftDeleteModel):

    lead = models.ForeignKey(
        "leads.Lead", on_delete=models.CASCADE, related_name="activities"
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="activities",
    )

    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)

    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    due_date = models.DateTimeField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    attachment = models.FileField(upload_to="lead-activities/", null=True, blank=True)

    objects = SoftDeleteManager()  # default
    all_objects = models.Manager()  # includes deleted lead_activities

    class Meta:
        ordering = ["-created_at", "due_date"]
        db_table = "lead_activity"

        indexes = [
            models.Index(fields=["is_completed"]),
            models.Index(fields=["workspace", "due_date"]),
            models.Index(fields=["workspace", "is_completed"]),
            models.Index(fields=["workspace", "created_at"]),
        ]

    def mark_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["is_completed", "completed_at"])

    def soft_delete(self):
        super().soft_delete()

        # 🔁 Cascade to attachments
        self.attachments.all().update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        super().restore()
        self.attachments.all().update(is_deleted=False, deleted_at=None)

    def __str__(self):
        return f"{self.activity_type} - {self.subject}"


class LeadActivityAttachment(TimeStampedModel, SoftDeleteModel):
    activity = models.ForeignKey(
        LeadActivity, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="lead-activity/")

    objects = SoftDeleteManager()  # default
    all_objects = models.Manager()

    def soft_delete(self):
        super().soft_delete()

    def restore(self):
        super().restore()

    class Meta:
        db_table = "lead_activity_attachment"

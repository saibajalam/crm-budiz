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

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_deals",
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

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

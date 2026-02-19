from django.db import models
from workspaces.models import Workspace
from django.conf import settings
from common.models import TimeStampedModel
from .constants import TRIGGERS, ACTION_CHOICES


# Create your models here.

User = settings.AUTH_USER_MODEL


class AutomationRule(TimeStampedModel):

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="automation_rules",
    )

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    event_name = models.CharField(max_length=255, choices=[(e, e) for e in TRIGGERS])
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "automation_rules"

    def __str__(self):
        return self.name


class AutomationCondition(TimeStampedModel):

    rule = models.ForeignKey(
        AutomationRule, related_name="conditions", on_delete=models.CASCADE
    )

    field = models.CharField(max_length=100)
    operator = models.CharField(max_length=50)
    value = models.JSONField()

    class Meta:
        db_table = "automation_conditions"


class AutomationAction(TimeStampedModel):

    rule = models.ForeignKey(
        AutomationRule, related_name="actions", on_delete=models.CASCADE
    )

    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    config = models.JSONField(default=dict)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "automation_actions"


class AutomationExecutionLog(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="automation_logs"
    )

    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="execution_logs",
    )

    # WHAT triggered this
    event_type = models.CharField(
        max_length=100, choices=[(e, e) for e in TRIGGERS], blank=True
    )

    # object reference
    target_object_id = models.IntegerField(null=True, blank=True)
    target_model = models.CharField(max_length=50, null=True, blank=True)

    # which action executed
    action_type = models.CharField(max_length=100, choices=ACTION_CHOICES, blank=True)

    # execution result
    status = models.CharField(
        max_length=20,
        choices=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
        ],
        default="success",
    )

    error_message = models.TextField(null=True, blank=True)
    error_trace = models.TextField(null=True, blank=True)

    # payload snapshot
    payload = models.JSONField(default=dict)

    # metadata (extra)
    metadata = models.JSONField(default=dict, blank=True)

    # retry safety
    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
    )

    # performance tracking
    duration_ms = models.IntegerField(null=True, blank=True)

    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_execution_logs"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["workspace", "rule"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["idempotency_key"]),
        ]

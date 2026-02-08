from django.db import models
from workspaces.models import Workspace
from django.conf import settings
from common.models import TimeStampedModel

# Create your models here.

User = settings.AUTH_USER_MODEL


class AutomationRule(TimeStampedModel):

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    trigger = models.CharField(max_length=50)

    class Meta:
        db_table = "automation_rules"

    def __str__(self):
        return self.name


class AutomationCondition(TimeStampedModel):

    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE)

    field = models.CharField(max_length=100)
    operator = models.CharField(max_length=50)
    value = models.JSONField()

    class Meta:
        db_table = "automation_conditions"


class AutomationAction(TimeStampedModel):
    from .constants import ACTION_CHOICES

    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE)

    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    params = models.JSONField(default=dict)

    class Meta:
        db_table = "automation_actions"


class AutomationExecutionLog(TimeStampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE)

    object_id = models.IntegerField()

    model_name = models.CharField(max_length=50)
    executed_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=50)
    message = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "automation_execution_logs"

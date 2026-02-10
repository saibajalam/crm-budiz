from django.db import models
from workspaces.models import Workspace
from django.conf import settings
from common.models import TimeStampedModel
from core.constants import PRIORITY_CHOICES

# Create your models here.

User = settings.AUTH_USER_MODEL


class Task(TimeStampedModel):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ]
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="open")
    due_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, null=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_tasks",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )

    related_object_id = models.IntegerField(null=True, blank=True)
    related_to_type = models.CharField(max_length=50, null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tasks"

    def __str__(self):
        return self.title

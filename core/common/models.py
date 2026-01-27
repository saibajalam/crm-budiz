from django.db import models

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WorkspaceCounter(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="counters"
    )
    entity = models.CharField(
        max_length=20,
        choices=[
            ("deal", "Deal"),
            ("lead", "Lead"),
        ]
    )
    current_value = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("workspace", "entity")
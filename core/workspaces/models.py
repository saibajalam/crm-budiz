from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from common.managers import SoftDeleteManager
from django.utils import timezone

# Create your models here.

class Workspace(TimeStampedModel):
    name = models.CharField(max_length = 255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "owned_workspaces",
    )

    objects = models.Manager()

    class Meta:
        db_table = "workspace"

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])



class WorkspaceMember(TimeStampedModel):
    
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("sales_representative", "SalesRepresentative"),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete= models.CASCADE,
        related_name= "members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_membership"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="sales_representative"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workspace_member"
        unique_together = ("workspace", "user")

    def __str__(self):
        return f"{self.user} → {self.workspace} ({self.role})"
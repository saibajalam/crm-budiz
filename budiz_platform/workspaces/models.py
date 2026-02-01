import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from django.utils import timezone
from .choices import WorkspaceRole
from datetime import timedelta


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
        ("member", "Member"),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete= models.CASCADE,
        related_name= "members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_members"
    )

    role = models.CharField(
        max_length=20,
        choices=WorkspaceRole.CHOICES,
        default=WorkspaceRole.SALES
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invite"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workspace_member"
        unique_together = ("workspace", "user")

    def __str__(self):
        return f"{self.user} → {self.workspace} ({self.role})"
    


class WorkspaceInvite(TimeStampedModel):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("member", "Member"),
    ]

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="invites"
    )

    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_workspace_invites"
    )

    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField()

    class Meta:
        db_table = "workspace_invite"
        unique_together = ("workspace", "email")

    def is_expired(self):
        return timezone.now > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def mark_accepted(self):
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save(update_fields=["is_accepted", "accepted_at"])

    def __str__(self):
        return f"{self.email} → {self.workspace.name}"

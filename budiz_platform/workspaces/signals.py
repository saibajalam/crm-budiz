from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Workspace, WorkspaceMember
from .choices import WorkspaceRole


@receiver(post_save, sender=Workspace)
def add_owner_as_member(sender, instance, created, **kwargs):
    if created:
        WorkspaceMember.objects.create(
            user=instance.owner,
            workspace=instance,
            role=WorkspaceRole.OWNER
        )

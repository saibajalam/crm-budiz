from django.db import models
from django.contrib.auth import get_user_model
from workspaces.models import Workspace

User = get_user_model()
# Create your models here.

class Contact(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=False, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)

    company = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
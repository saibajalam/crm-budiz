from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
import uuid
from django.utils import timezone
from datetime import timedelta


# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel) :
    email = models.EmailField(unique= True, null= False)
    phone_number = models.CharField(
    max_length=15,
    unique=True,
    null=False,
    blank=False
)
    full_name = models.CharField(max_length= 100)
    is_active = models.BooleanField(default= True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default= False)
    date_joined = models.DateTimeField(auto_now_add= True)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email
    
    def get_roles(self):
        return self.userrole_set.values_list('role__name', flat=True)

    def has_role(self, role_name):
        return self.userrole_set.filter(role__name=role_name).exists()
    
    

class Role(TimeStampedModel) :
    name = models.CharField(max_length= 100, unique= True)
    description = models.TextField(blank= True)

    def __str__(self):
        return self.name
    

class UserRole(TimeStampedModel) :
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    role = models.ForeignKey(Role, on_delete= models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')


class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(minutes=15)
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    

class EmailVerificationToken(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(hours=24)

    def __str__(self):
        return f"{self.user.email} - {self.token}"
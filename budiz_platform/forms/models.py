from django.db import models
from django.conf import settings
from common.models import TimeStampedModel

# Create your models here.


class Form(TimeStampedModel):

    DUPLICATE_CHOICES = [
        ("create", "Always create new lead"),
        ("update", "Update existing lead"),
        ("configurable", "Smart match email/phone"),
    ]

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="forms",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    duplicate_handling = models.CharField(
        max_length=20, choices=DUPLICATE_CHOICES, default="configurable"
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = "forms"


class FormField(TimeStampedModel):

    FIELD_TYPES = [
        ("text", "Text"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("textarea", "Textarea"),
        ("select", "Select"),
        ("checkbox", "Checkbox"),
    ]

    LEAD_FIELD_MAP = [
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("company", "Company"),
        ("job_title", "Job Title"),
        ("notes", "Notes"),
        ("none", "No Mapping"),
    ]

    ASSIGNMENT_CHOICES = [
        ("none", "No auto assignment"),
        ("fixed", "Assign to fixed user"),
        ("round_robin", "Round robin"),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="fields")

    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    options = models.TextField(blank=True, null=True)

    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    map_to_lead_field = models.CharField(
        max_length=50, choices=LEAD_FIELD_MAP, default="none"
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_CHOICES,
        default="none",
    )

    fixed_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="form_fixed_assignments",
    )

    round_robin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="form_round_robin",
    )

    round_robin_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "form_fields"


class FormSubmission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="submissions")
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.CASCADE)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    lead = models.ForeignKey(
        "leads.Lead", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "form_submissions"
        indexes = [
            models.Index(fields=["form", "submitted_at"]),
            models.Index(fields=["workspace", "submitted_at"]),
            models.Index(fields=["lead"]),
        ]


class FormResponse(TimeStampedModel):
    submission = models.ForeignKey(
        FormSubmission, on_delete=models.CASCADE, related_name="responses"
    )
    field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="responses"
    )

    value = models.TextField()

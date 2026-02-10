from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "workspace",
        "status",
        "priority",
        "assigned_to",
        "created_by",
        "due_at",
        "completed_at",
    )
    list_filter = ("status", "priority", "workspace")
    search_fields = ("title", "description")

from django.contrib import admin
from .models import (
    AutomationRule,
    AutomationCondition,
    AutomationAction,
    AutomationExecutionLog,
)


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "workspace", "is_active", "event_name", "created_by")


@admin.register(AutomationCondition)
class AutomationConditionAdmin(admin.ModelAdmin):
    list_display = ("rule", "field", "operator", "value")


@admin.register(AutomationAction)
class AutomationActionAdmin(admin.ModelAdmin):
    list_display = ("rule", "action_type", "config", "order")


@admin.register(AutomationExecutionLog)
class AutomationExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "workspace",
        "rule",
        "target_model",
        "target_object_id",
        "executed_at",
        "status",
        "error_message",
        "error_trace",
    )

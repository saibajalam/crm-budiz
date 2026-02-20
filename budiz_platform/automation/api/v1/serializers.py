from rest_framework import serializers
from automation.models import (
    AutomationRule,
    AutomationCondition,
    AutomationAction,
    AutomationExecutionLog,
)
from automation.constants import TRIGGERS, ACTION_CHOICES, OPERATORS


# ---------------------------
# CONDITION
# ---------------------------
class AutomationConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationCondition
        fields = ["id", "rule", "field", "operator", "value"]

    def validate_operator(self, val):
        if val not in OPERATORS:
            raise serializers.ValidationError("Invalid operator")
        return val


# ---------------------------
# ACTION
# ---------------------------
class AutomationActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationAction
        fields = ["id", "rule", "action_type", "config", "order"]

    def validate_action_type(self, val):
        action_types = {choice[0] for choice in ACTION_CHOICES}
        if val not in action_types:
            raise serializers.ValidationError("Invalid action type")
        return val


# ---------------------------
# RULE
# ---------------------------
class AutomationRuleSerializer(serializers.ModelSerializer):
    conditions = AutomationConditionSerializer(
        many=True,
        source="conditions",
    )
    actions = AutomationActionSerializer(
        many=True,
        source="actions",
    )

    class Meta:
        model = AutomationRule
        fields = [
            "id",
            "name",
            "event_name",
            "is_active",
            "created_by",
            "conditions",
            "actions",
        ]

    def validate_event_name(self, val):
        trigger_value = val if isinstance(val, str) else val.get("event_name")
        if trigger_value not in TRIGGERS:
            raise serializers.ValidationError("Invalid event name")
        return val

    def create(self, validated_data):
        conditions_data = validated_data.pop("conditions", [])
        actions_data = validated_data.pop("actions", [])

        workspace = self.context["workspace"]
        created_by = self.context.get("user")
        if created_by is None:
            request = self.context.get("request")
            created_by = getattr(request, "user", None)

        if created_by is not None and getattr(created_by, "is_authenticated", False):
            validated_data["created_by"] = created_by

        rule = AutomationRule.objects.create(
            workspace=workspace,
            **validated_data,
        )

        for c in conditions_data:
            AutomationCondition.objects.create(rule=rule, **c)

        for a in actions_data:
            AutomationAction.objects.create(rule=rule, **a)

        return rule

    def update(self, instance, validated_data):
        conditions_data = validated_data.pop("conditions", None)
        actions_data = validated_data.pop("actions", None)

        instance.name = validated_data.get("name", instance.name)
        instance.event_name = validated_data.get("event_name", instance.event_name)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()

        if conditions_data is not None:
            instance.conditions.all().delete()
            for c in conditions_data:
                AutomationCondition.objects.create(rule=instance, **c)

        if actions_data is not None:
            instance.actions.all().delete()
            for a in actions_data:
                AutomationAction.objects.create(rule=instance, **a)

        return instance


class AutomationExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationExecutionLog
        fields = [
            "id",
            "workspace",
            "rule",
            "event_type",
            "action_type",
            "payload",
            "target_object_id",
            "status",
            "error_message",
            "error_trace",
            "metadata",
            "idempotency_key",
            "duration_ms",
            "executed_at",
        ]

        read_only_fields = fields

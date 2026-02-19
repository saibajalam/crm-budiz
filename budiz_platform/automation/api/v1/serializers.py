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
        fields = ["id", "field", "operator", "value"]

    def validate_operator(self, val):
        if val not in OPERATORS:
            raise serializers.ValidationError("Invalid operator")
        return val


# ---------------------------
# ACTION
# ---------------------------
class AutomationActionSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()

    class Meta:
        model = AutomationAction
        fields = ["id", "action_type", "config"]

    def validate_action_type(self, val):
        action_types = {choice[0] for choice in ACTION_CHOICES}
        if val not in action_types:
            raise serializers.ValidationError("Invalid action type")
        return val


# ---------------------------
# RULE
# ---------------------------
class AutomationRuleSerializer(serializers.ModelSerializer):
    trigger = serializers.ChoiceField(source="event_name", choices=TRIGGERS)
    conditions = AutomationConditionSerializer(
        many=True,
        source="automationcondition_set",
    )
    actions = AutomationActionSerializer(
        many=True,
        source="automationaction_set",
    )

    class Meta:
        model = AutomationRule
        fields = [
            "id",
            "name",
            "trigger",
            "is_active",
            "conditions",
            "actions",
        ]

    def validate_trigger(self, val):
        trigger_value = val if isinstance(val, str) else val.get("event_name")
        if trigger_value not in TRIGGERS:
            raise serializers.ValidationError("Invalid trigger")
        return val

    def create(self, validated_data):
        conditions_data = validated_data.pop("automationcondition_set", [])
        actions_data = validated_data.pop("automationaction_set", [])

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
        conditions_data = validated_data.pop("automationcondition_set", None)
        actions_data = validated_data.pop("automationaction_set", None)

        instance.name = validated_data.get("name", instance.name)
        instance.event_name = validated_data.get("event_name", instance.event_name)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()

        if conditions_data is not None:
            instance.automationcondition_set.all().delete()
            for c in conditions_data:
                AutomationCondition.objects.create(rule=instance, **c)

        if actions_data is not None:
            instance.automationaction_set.all().delete()
            for a in actions_data:
                AutomationAction.objects.create(rule=instance, **a)

        return instance


class AutomationExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationExecutionLog
        fields = [
            "id",
            "rule",
            "object_id",
            "model_name",
            "status",
            "success",
            "message",
            "metadata",
            "executed_at",
        ]

        read_only_fields = fields

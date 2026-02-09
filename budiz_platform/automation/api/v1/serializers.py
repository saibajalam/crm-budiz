from rest_framework import serializers
from automation.models import (
    AutomationRule,
    AutomationCondition,
    AutomationAction,
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
    class Meta:
        model = AutomationAction
        fields = ["id", "action_type", "params"]

    def validate_action_type(self, val):
        if val not in ACTION_CHOICES:
            raise serializers.ValidationError("Invalid action type")
        return val


# ---------------------------
# RULE
# ---------------------------
class AutomationRuleSerializer(serializers.ModelSerializer):
    conditions = AutomationConditionSerializer(many=True)
    actions = AutomationActionSerializer(many=True)

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
        if val not in TRIGGERS:
            raise serializers.ValidationError("Invalid trigger")
        return val

    def create(self, validated_data):
        conditions_data = validated_data.pop("conditions", [])
        actions_data = validated_data.pop("actions", [])

        workspace = self.context["workspace"]

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
        instance.trigger = validated_data.get("trigger", instance.trigger)
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

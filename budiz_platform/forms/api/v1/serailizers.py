from rest_framework import serializers
from ...models import Form, FormField


class PublicFormSubmitSerializer(serializers.Serializer):
    data = serializers.DictField()

    def validate(self, attrs):
        form = self.context["form"]
        fields = form.fields.all()

        for field in fields:
            if field.is_required and field.label not in attrs["data"]:
                raise serializers.ValidationError(f"{field.label} is required")

        return attrs


class CreateFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ["id", "name", "duplicate_handling"]


class AddFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField
        fields = [
            "label",
            "field_type",
            "options",
            "is_required",
            "order",
            "map_to_lead_field",
        ]


class UpdateFormAssignmentSerializer(serializers.Serializer):
    assignment_type = serializers.ChoiceField(choices=["none", "fixed", "round_robin"])
    fixed_assignee_id = serializers.IntegerField(required=False)
    round_robin_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

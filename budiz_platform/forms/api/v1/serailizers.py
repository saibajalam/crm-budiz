from rest_framework import serializers
from django.db import transaction
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


class CreateFormWithFieldsSerializer(serializers.ModelSerializer):
    fields = AddFieldSerializer(many=True, required=False)

    class Meta:
        model = Form
        fields = ["id", "name", "duplicate_handling", "fields"]

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        with transaction.atomic():
            form = Form.objects.create(**validated_data)

            for field_data in fields_data:
                FormField.objects.create(form=form, **field_data)

            return form


class UpdateFormAssignmentSerializer(serializers.Serializer):
    assignment_type = serializers.ChoiceField(choices=["none", "fixed", "round_robin"])
    fixed_assignee_id = serializers.IntegerField(required=False)
    round_robin_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

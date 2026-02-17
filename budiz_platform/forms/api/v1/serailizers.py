from rest_framework import serializers
from django.db import transaction
from ...models import Form, FormField


class PublicFormSubmitSerializer(serializers.Serializer):
    data = serializers.DictField()

    def validate(self, attrs):
        form = self.context["form"]
        fields = form.fields.all()
        data = attrs.get("data", {})

        def normalize_label(label):
            return " ".join(str(label).strip().lower().replace("_", " ").split())

        def has_key(key):
            return key in normalized_data

        def has_any(*keys):
            return any(has_key(key) for key in keys)

        normalized_data = {normalize_label(key): value for key, value in data.items()}

        if not has_any("full name", "full_name"):
            raise serializers.ValidationError("full name is required")

        if not has_any("email"):
            raise serializers.ValidationError("email is required")

        if not has_any("phone", "phone number", "phone_number"):
            raise serializers.ValidationError("phone is required")

        for field in fields:
            field_key = normalize_label(field.label)
            if not field.is_required:
                continue

            if field_key in {"first name", "last name"}:
                if not has_any(field_key, "full name"):
                    raise serializers.ValidationError(f"{field.label} is required")
                continue

            if field_key == "full name":
                if not has_any("full name", "first name", "last name"):
                    raise serializers.ValidationError("full name is required")
                continue

            if field_key in {"phone", "phone number"}:
                if not has_any("phone", "phone number"):
                    raise serializers.ValidationError(f"{field.label} is required")
                continue

            if field_key not in normalized_data:
                raise serializers.ValidationError(f"{field.label} is required")

        attrs["data"] = normalized_data

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

    @staticmethod
    def _detect_lead_mapping(label, field_type):
        normalized_label = " ".join(str(label or "").strip().lower().split())
        compact_label = normalized_label.replace("_", " ")

        if compact_label in {"first name", "firstname"}:
            return "first_name"
        if compact_label in {"last name", "lastname"}:
            return "last_name"
        if "email" in compact_label:
            return "email"
        if compact_label in {"phone", "phone number"} or "phone" in compact_label:
            return "phone"

        if field_type == "email":
            return "email"
        if field_type == "phone":
            return "phone"

        return "none"

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        with transaction.atomic():
            form = Form.objects.create(**validated_data)

            for field_data in fields_data:
                field_payload = dict(field_data)
                map_to_lead_field = field_payload.get("map_to_lead_field", "none")

                if map_to_lead_field == "none":
                    field_payload["map_to_lead_field"] = self._detect_lead_mapping(
                        field_payload.get("label"),
                        field_payload.get("field_type"),
                    )

                FormField.objects.create(form=form, **field_payload)

            return form


class UpdateFormAssignmentSerializer(serializers.Serializer):
    assignment_type = serializers.ChoiceField(choices=["none", "fixed", "round_robin"])
    fixed_assignee_id = serializers.IntegerField(required=False)
    round_robin_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

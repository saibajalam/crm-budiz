from rest_framework import serializers
from .models import Deal
from django.contrib.auth import get_user_model
from common.serializers import SimpleUserSerializer

User = get_user_model()

PIPELINE_STAGES = [
    "lead",
    "contact_made",
    "proposal_sent",
    "negotiation",
    "closed_won",
    "closed_lost",
]


class CreateDealSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Deal
        fields = (
            "id",
            "title",
            "value",
            "probability",
            "pipeline_stage",
            "expected_close_date",
            "assigned_to_id",
            "notes",
            "full_name",
        )

    def validate_probability(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Probability must be between 0 and 100.")
        return value

    def validate_assigned_to_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid team member.")
        return value

    def create(self, validated_data):
        assigned_to_id = validated_data.pop("assigned_to_id", None)

        assigned_to = None
        if assigned_to_id:
            assigned_to = User.objects.get(id=assigned_to_id)

        deal = Deal.objects.create(
            **validated_data,
            assigned_to=assigned_to,
            created_by=self.context["request"].user
        )

        return deal


class DealDetailSerializer(serializers.ModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True, allow_null=True)
    pipeline_stage_display = serializers.CharField(
        source="get_pipeline_stage_display", read_only=True
    )

    class Meta:
        model = Deal
        fields = [
            "id",
            "title",
            "value",
            "probability",
            "pipeline_stage_display",
            "expected_close_date",
            "assigned_to",
            "notes",
        ]
        read_only_fields = fields


class DealUpdateSerializer(serializers.ModelSerializer):

    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id",
            "title",
            "value",
            "probability",
            "pipeline_stage",
            "expected_close_date",
            "assigned_to",
            "notes",
        ]

    extra_kwargs = {
        "title": {"required": False},
        "value": {"required": False},
        "probability": {"required": False},
        "pipeline_stage": {"required": False},
        "expected_close_date": {"required": False},
        "assigned_to": {"required": False},
        "notes": {"required": False},
    }

    def validate_pipeline_stage(self, value):
        if value not in PIPELINE_STAGES:
            raise serializers.ValidationError("Invalid pipeline stage.")
        return value


class DealPipelineSerializer(serializers.ModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id",
            "title",
            "value",
            "probability",
            "pipeline_stage",
            "expected_close_date",
            "assigned_to",
            "notes",
        ]


class DealAssignmentSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Deal
        fields = ["assigned_to_id"]

    def validate_assigned_to_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Assigned user does not exist.")
        return value

    def update(self, instance, validated_data):
        user_id = validated_data.get("assigned_to_id")
        if user_id:
            from accounts.models import User

            user = User.objects.get(id=user_id)
            instance.assigned_to = user
            instance.save()
        return instance

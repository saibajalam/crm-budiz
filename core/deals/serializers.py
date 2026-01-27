from rest_framework import serializers
from .models import Deal
from django.contrib.auth import get_user_model
from common.serializers import SimpleUserSerializer
from workspaces.models import WorkspaceMember
from common.counter import get_next_display_number
from common.utils import format_display_number

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
    assigned_to = serializers.IntegerField(
        required=False,
        write_only=True
    )
    display_id = serializers.ReadOnlyField()


    class Meta:
        model = Deal
        fields = (
            "id",
            "title",
            "value",
            "probability",
            "pipeline_stage",
            "expected_close_date",
            "assigned_to",
            "notes",
        )

    def validate_probability(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError(
                "Probability must be between 0 and 100."
            )
        return value

    def validate_assigned_to(self, value):
        workspace = self.context["workspace"]

        try:
            member = WorkspaceMember.objects.get(
                workspace=workspace,
                user_id=value,
                is_active=True,
            )
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError(
                "Assigned user is not a member of this workspace."
            )

        return member.user  # return User instance
    
    def get_formatted_number(self, obj):
        return format_display_number("DEAL", obj.display_number)

    def create(self, validated_data):
        request = self.context["request"]
        workspace = self.context["workspace"]

        assigned_to = validated_data.pop("assigned_to", None)

        display_number = get_next_display_number(workspace, "deal")

        return Deal.objects.create(
            **validated_data,
            workspace=workspace,
            display_number=display_number,
            assigned_to=assigned_to,
            created_by=request.user,
        )



class DealDetailSerializer(serializers.ModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True, allow_null=True)
    pipeline_stage_display = serializers.CharField(
        source="get_pipeline_stage_display", read_only=True
    )
    workspace = serializers.StringRelatedField()

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
            "workspace",
        ]
        read_only_fields = fields

    def validate_assigned_to(self, user):
        deal = self.instance  # IMPORTANT
        workspace = deal.workspace

        if not WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "You can only see deal_details of the same workspace."
            )

        return user


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
    
    def validate_assigned_to(self, user):
        deal = self.instance  # IMPORTANT
        workspace = deal.workspace

        if not WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "You can only update deals of the same workspace."
            )

        return user


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
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="assigned_to",
    )

    class Meta:
        model = Deal
        fields = ["assigned_to_id"]

    def validate_assigned_to_id(self, user):
        deal = self.instance  # IMPORTANT
        workspace = deal.workspace

        if not WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "You can only assign deals to members of the same workspace."
            )

        return user


from rest_framework import serializers
from ...models import Lead, LeadActivity
from common.counter import get_next_display_number
from common.utils import format_display_number
from django.utils import timezone
from deals.models import Deal, DealActivity
from common.email_utils import (
    send_lead_conversion_notification,
    send_lead_conversion_confirmation,
)
from workspaces.models import WorkspaceMember
from decimal import Decimal
from django.db import transaction
from leads.services.lead_service import create_lead
from typing import Any, Dict, List, Optional


class CreateLeadSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    document = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Lead
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "job_title",
            "status",
            "source",
            "score",
            "image",
            "document",
        ]
        read_only_fields = ["score"]

    def create(self, validated_data):
        workspace = validated_data.pop("workspace", None) or self.context.get(
            "workspace"
        )
        if not workspace:
            raise serializers.ValidationError("Workspace context required")

        request = self.context.get("request")
        user = request.user if request else validated_data.pop("created_by", None)
        if not user:
            raise serializers.ValidationError("User context required")

        display_number = get_next_display_number(workspace, "lead")
        validated_data["display_number"] = display_number
        return create_lead(
            workspace=workspace,
            payload=validated_data,
            created_by=user,
        )


class LeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "job_title",
            "status",
            "source",
            "image",
            "document",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def validate_status(self, value):
        allowed_statuses = ["new", "contacted", "qualified", "lost"]
        if value not in allowed_statuses:
            raise serializers.ValidationError("Invalid lead status.")
        return value


class LeadActivityCreateSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField(write_only=True)

    activity_type = serializers.ChoiceField(
        choices=["call", "email", "meeting", "note", "task"], default="email"
    )

    priority = serializers.ChoiceField(
        choices=["low", "medium", "high"], default="medium"
    )

    subject = serializers.CharField(max_length=255)

    description = serializers.CharField(required=False, allow_blank=True)

    due_date = serializers.DateTimeField(required=False)

    attachment = serializers.FileField(required=False)

    # resolved object (internal use)
    lead = serializers.HiddenField(default=None)

    def validate_lead_id(self, value):
        try:
            lead = Lead.objects.get(id=value)
        except Lead.DoesNotExist:
            raise serializers.ValidationError("Invalid lead")

        # store resolved lead object
        self._validated_lead = lead
        return value

    def validate(self, attrs):
        # attach lead object to validated data
        attrs["lead"] = self._validated_lead
        return attrs


class LeadActivityUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeadActivity
        fields = (
            "activity_type",
            "priority",
            "subject",
            "description",
            "due_date",
        )

    # activity_type = serializers.ChoiceField(
    #     choices=LeadActivity.ACTIVITY_TYPES,
    #     required=False
    # )
    # priority = serializers.ChoiceField(
    #     choices=LeadActivity.PRIORITY_CHOICES,
    #     required=False
    # )
    # subject = serializers.CharField(max_length=255, required=False)
    # description = serializers.CharField(required=False, allow_blank=True)
    # due_date = serializers.DateTimeField(required=False)
    # attachments = serializers.ListField(
    #     child=serializers.FileField(),
    #     required=False
    # )


class LeadListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lead
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "status",
            "source",
            "score",
            "created_at",
        )
        read_only_fields = fields


class LeadDetailSerializer(serializers.ModelSerializer):

    created_by = serializers.SerializerMethodField()
    workspace = serializers.StringRelatedField()

    class Meta:
        model = Lead
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "job_title",
            "status",
            "source",
            "score",
            "created_at",
            "updated_at",
            "created_by",
            "workspace",
        )

        read_only_fields = fields

    def get_created_by(self, obj) -> Optional[Dict[str, Any]]:
        if obj.created_by:
            return {
                "user_id": obj.created_by.id,
                "email": obj.created_by.email,
            }
        return None


class LeadActivityListSerializer(serializers.ModelSerializer):
    performed_by = serializers.SerializerMethodField()
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = LeadActivity
        fields = (
            "id",
            "activity_type",
            "priority",
            "subject",
            "description",
            "due_date",
            "performed_by",
            "created_at",
            "attachment",
        )

        read_only_fields = fields

    def get_performed_by(self, obj) -> Optional[Dict[str, Any]]:
        user = obj.performed_by
        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
        }

    def get_attachment(self, obj) -> List[str]:
        request = self.context.get("request")
        files = obj.attachments.all()  # use the related_name
        return [
            request.build_absolute_uri(f.file.url) if request else f.file.url
            for f in files
        ]


class LeadActivityFeedSerializer(serializers.ModelSerializer):
    is_upcoming = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    lead_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadActivity
        fields = [
            "id",
            "subject",
            "due_date",
            "activity_type",
            "lead_name",
            "is_upcoming",
            "is_overdue",
            "is_completed",
        ]

    def get_lead_name(self, obj) -> str:
        return f"{obj.lead.first_name} {obj.lead.last_name}"

    def get_is_upcoming(self, obj) -> bool:
        return obj.due_date > timezone.now() and not obj.is_completed

    def get_is_overdue(self, obj) -> bool:
        return obj.due_date < timezone.now() and not obj.is_completed

    def get_is_completed(self, obj) -> bool:
        return obj.is_completed


class LeadConversionSerializer(serializers.Serializer):
    """
    Serializer for converting a lead to a deal.
    Validates business rules and creates the deal with transferred activities.
    """

    # Deal details (optional, with defaults)
    title = serializers.CharField(max_length=255, required=False)
    value = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    probability = serializers.IntegerField(required=False, min_value=0, max_value=100)
    expected_close_date = serializers.DateField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    # Internal fields for validation
    lead = serializers.HiddenField(default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set defaults for optional fields
        if "data" in kwargs:
            data = kwargs["data"].copy()
            if "title" not in data or not data.get("title"):
                # Generate default title from lead name
                lead = kwargs.get("context", {}).get("lead")
                if lead:
                    data["title"] = f"Deal from {lead.first_name} {lead.last_name}"
            if "value" not in data or not data.get("value"):
                data["value"] = Decimal("0.00")
            if "probability" not in data or data.get("probability") is None:
                data["probability"] = 50
            kwargs["data"] = data

    def validate_assigned_to(self, value):
        """Validate that assigned user exists and is in the workspace"""
        workspace = self.context.get("workspace")
        if not workspace:
            raise serializers.ValidationError("Workspace context required")

        try:
            from workspaces.models import WorkspaceMember

            member = WorkspaceMember.objects.get(workspace=workspace, user_id=value)
            return member.user
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError(
                "Assigned user is not a member of this workspace"
            )

    def validate(self, attrs):
        """Validate conversion business rules"""
        lead = self.context.get("lead")
        if not lead:
            raise serializers.ValidationError("Lead context required")

        # Check if lead can be converted
        if lead.status != "qualified":
            raise serializers.ValidationError(
                "Only qualified leads can be converted to deals"
            )

        if lead.is_converted:
            raise serializers.ValidationError("Lead has already been converted")

        # Set defaults if not provided
        if "title" not in attrs or not attrs["title"]:
            attrs["title"] = f"Deal from {lead.first_name} {lead.last_name}"

        if "value" not in attrs:
            attrs["value"] = Decimal("0.00")

        if "probability" not in attrs:
            attrs["probability"] = 50

        return attrs

    def create(self, validated_data):
        """Create deal and transfer activities"""

        lead = self.context["lead"]
        workspace = self.context["workspace"]
        user = self.context["request"].user

        # Create the deal
        deal_data = {
            "title": validated_data["title"],
            "value": validated_data["value"],
            "probability": validated_data["probability"],
            "expected_close_date": validated_data.get("expected_close_date"),
            "assigned_to": validated_data.get("assigned_to"),
            "notes": validated_data.get("notes", ""),
            "workspace": workspace,
            "created_by": user,
            "created_from_lead": lead,
            "display_number": get_next_display_number(workspace, "deal"),
        }

        with transaction.atomic():
            deal = Deal.objects.create(**deal_data)

        # Transfer lead activities to deal activities
        lead_activities = lead.activities.filter(is_deleted=False)
        for lead_activity in lead_activities:
            DealActivity.objects.create(
                title=lead_activity.subject,
                description=lead_activity.description,
                due_date=lead_activity.due_date,
                status="pending",  # Reset status for new deal
                activity_type=lead_activity.activity_type,
                assigned_to=lead_activity.performed_by or user,
                deal=deal,
                workspace=workspace,
                created_at=lead_activity.created_at,  # Preserve original creation time
            )

        # Mark lead as converted
        lead.status = "converted"
        lead.is_converted = True
        lead.save(update_fields=["status", "is_converted"])

        # Send email notifications
        # try:
        #     # Send notification to other workspace members
        #     send_lead_conversion_notification(lead, deal, user)
        #     # Send confirmation to the user who performed the conversion
        #     send_lead_conversion_confirmation(lead, deal, user)
        # except Exception as e:
        #     # Log email failure but don't fail the conversion
        #     import logging

        #     logger = logging.getLogger(__name__)
        #     logger.warning(f"Failed to send conversion emails: {e}")

        return deal

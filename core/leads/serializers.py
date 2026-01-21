from rest_framework import serializers
from .models import Lead, LeadActivity


class CreateLeadSerializer(serializers.ModelSerializer):
    # Optional file uploads
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
        read_only_fields = ["score"]  # score can be managed internally

    def create(self, validated_data):
        user = self.context["request"].user
        # Automatically assign the creator
        return Lead.objects.create(created_by=user, **validated_data)



class LeadActivityCreateSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField(write_only=True)

    activity_type = serializers.ChoiceField(
        choices=["call", "email", "meeting", "note", "task"]
    )

    priority = serializers.ChoiceField(
        choices=["low", "medium", "high"],
        default="medium"
    )

    subject = serializers.CharField(max_length=255)

    description = serializers.CharField(
        required=False,
        allow_blank=True
    )

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
    


class LeadActivityUpdateSerializer(serializers.Serializer):
    activity_type = serializers.ChoiceField(
        choices=LeadActivity.ACTIVITY_TYPES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=LeadActivity.PRIORITY_CHOICES,
        required=False
    )
    subject = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )



class LeadListSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

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

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"



class LeadDetailSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

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
            "description",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_created_by(self, obj):
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "name": obj.created_by.get_full_name()
                if hasattr(obj.created_by, "get_full_name")
                else obj.created_by.email,
                "email": obj.created_by.email,
            }
        return None
    

class LeadActivityListSerializer(serializers.ModelSerializer):
    performed_by = serializers.SerializerMethodField()
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            "id",
            "activity_type",
            "priority",
            "subject",
            "description",
            "due_date",
            "performed_by",
            "created_at",
            "attachment"
        )

        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_performed_by(self, obj):
        user = obj.performed_by

        if not user :
            return None
        return {
            "id": user.id,
            "name": user.get_full_name()
            if hasattr(user, "get_full_name")
            else user.email,
            "email": user.email,
        }
    
    def get_attachment(self, obj):
        if obj.attachment:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url
        return None
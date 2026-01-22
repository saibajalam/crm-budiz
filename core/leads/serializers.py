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
        return Lead.objects.create(**validated_data)


class LeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "first_name",
            "last_name",
            "email",''
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
    


class LeadActivityUpdateSerializer(serializers.ModelSerializer):

    class Meta :
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
        )

        read_only_fields = fields

    
    def get_created_by(self, obj):
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
            "attachment"
        )

        read_only_fields = fields

    def get_performed_by(self, obj):
        user = obj.performed_by
        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
        }
    
    def get_attachment(self, obj):
        request = self.context.get("request")
        files = obj.attachments.all()  # use the related_name
        return [
            request.build_absolute_uri(f.file.url) if request else f.file.url
            for f in files
        ]
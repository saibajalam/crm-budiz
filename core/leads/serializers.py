from rest_framework import serializers
from .models import Lead


class AddLeadSerializer(serializers.ModelSerializer):
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
        ]


class LeadActivityCreateSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField()
    activity_type = serializers.ChoiceField(
        choices=["call", "email", "meeting", "note", "task"]
    )
    priority = serializers.ChoiceField(
        choices=["low", "medium", "high"],
        default="medium"
    )
    subject = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateTimeField(required=False)

    def validate_lead_id(self, value):
        if not Lead.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid lead")
        return value

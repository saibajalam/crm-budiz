from rest_framework import serializers
from contact.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "company",
            "position",
            "workspace",
            "created_by",
            "created_at",
            "is_deleted",
        ]
        read_only_fields = ["workspace", "created_by", "created_at", "is_deleted"]
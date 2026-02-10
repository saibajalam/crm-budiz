from rest_framework import serializers
from django.utils import timezone

from tasks.models import Task
from workspaces.models import WorkspaceMember
from django.contrib.auth import get_user_model


User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "due_at",
            "priority",
            "assigned_to_id",
            "created_by_id",
            "related_object_id",
            "related_to_type",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by_id",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def _validate_assigned_to(self, assigned_to_id, workspace):
        if assigned_to_id is None:
            return None

        if not User.objects.filter(id=assigned_to_id).exists():
            raise serializers.ValidationError("Assigned user not found")

        is_member = WorkspaceMember.objects.filter(
            workspace=workspace,
            user_id=assigned_to_id,
            is_active=True,
        ).exists()
        if not is_member:
            raise serializers.ValidationError("Assigned user is not in this workspace")

        return assigned_to_id

    def create(self, validated_data):
        workspace = self.context["workspace"]
        request = self.context.get("request")

        assigned_to_id = validated_data.pop("assigned_to_id", None)
        assigned_to_id = self._validate_assigned_to(assigned_to_id, workspace)

        status_value = validated_data.get("status")
        completed_at = None
        if status_value == "done":
            completed_at = timezone.now()

        task = Task.objects.create(
            workspace=workspace,
            created_by=request.user if request else None,
            assigned_to_id=assigned_to_id,
            completed_at=completed_at,
            **validated_data,
        )

        return task

    def update(self, instance, validated_data):
        workspace = instance.workspace

        assigned_to_id = validated_data.pop("assigned_to_id", None)
        if assigned_to_id is not None:
            assigned_to_id = self._validate_assigned_to(assigned_to_id, workspace)
            instance.assigned_to_id = assigned_to_id

        status_value = validated_data.get("status", instance.status)
        if status_value == "done":
            instance.completed_at = instance.completed_at or timezone.now()
        else:
            instance.completed_at = None

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance

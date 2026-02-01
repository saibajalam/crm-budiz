from rest_framework import serializers
from ...models import Workspace
from django.contrib.auth import get_user_model
from ...models import Workspace, WorkspaceMember, WorkspaceInvite

User = get_user_model()


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]

    def validate_slug(self, value):
        if Workspace.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "Workspace with this slug already exists."
            )
        return value


class WorkspaceEmailInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["owner", "admin", "manager", "member"])

    def validate(self, attrs):
        request = self.context["request"]
        inviter = request.user
        workspace = self.context["workspace"]
        email = attrs["email"]

        # Authorization FIRST
        try:
            member = WorkspaceMember.objects.get(
                workspace=workspace,
                user=inviter,
            )
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError("You are not a member of this workspace.")

        if member.role not in ["owner", "admin"]:
            raise serializers.ValidationError(
                "You do not have permission to invite users to this workspace."
            )

        # Self invite
        if email == inviter.email:
            raise serializers.ValidationError("You cannot invite yourself.")

        # Invitee check
        invitee = User.objects.filter(email=email).first()

        if invitee:
            if WorkspaceMember.objects.filter(
                user=invitee,
                is_active=True,
            ).exists():
                raise serializers.ValidationError("User is already in a workspace.")

        # Duplicate invite
        if WorkspaceInvite.objects.filter(
            workspace=workspace,
            email=email,
            is_accepted=False,
        ).exists():
            raise serializers.ValidationError("Invite already sent to this email.")

        attrs["workspace"] = workspace
        attrs["invited_by"] = inviter
        return attrs

    def create(self, validated_data):
        return WorkspaceInvite.objects.create(
            workspace=validated_data["workspace"],
            email=validated_data["email"],
            role=validated_data["role"],
            invited_by=validated_data["invited_by"],
        )


class WorkspaceMemberRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["admin", "member"])

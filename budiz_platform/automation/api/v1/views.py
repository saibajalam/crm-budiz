from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace

from drf_spectacular.utils import extend_schema, OpenApiResponse
from common.swagger import workspace_header

from automation.models import AutomationRule
from .serializers import AutomationRuleSerializer
from django.shortcuts import get_object_or_404


# ---------------------------
# LIST + CREATE
# ---------------------------
class AutomationRuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: AutomationRuleSerializer(many=True)},
        description="List all automation rules in the workspace",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        rules = AutomationRule.objects.filter(workspace=workspace)
        serializer = AutomationRuleSerializer(rules, many=True)

        return Response(serializer.data)

    @extend_schema(
        request=AutomationRuleSerializer,
        responses={201: AutomationRuleSerializer},
        description="Create a new automation rule",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request):
        workspace = get_user_workspace(request.user)

        serializer = AutomationRuleSerializer(
            data=request.data,
            context={"workspace": workspace},
        )
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()

        return Response(
            AutomationRuleSerializer(rule).data,
            status=status.HTTP_201_CREATED,
        )


class AutomationRuleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get_object(self, request, rule_id):
        workspace = get_user_workspace(request.user)

        return get_object_or_404(
            AutomationRule,
            id=rule_id,
            workspace=workspace,
        )

    @extend_schema(
        responses={200: AutomationRuleSerializer},
        description="Retrieve a specific automation rule",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        return Response(AutomationRuleSerializer(rule).data)

    @extend_schema(
        request=AutomationRuleSerializer,
        responses={200: AutomationRuleSerializer},
        description="Partially update an automation rule",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        serializer = AutomationRuleSerializer(
            rule,
            data=request.data,
            partial=True,
            context={"workspace": rule.workspace},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @extend_schema(
        responses={204: OpenApiResponse(description="Automation rule deleted")},
        description="Delete an automation rule",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def delete(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        rule.delete()
        return Response(status=204)


class ToggleAutomationRuleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Automation rule toggled")},
        description="Toggle automation rule active status",
        tags=["Automation"],
        auth=[{"BearerAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, rule_id):
        workspace = get_user_workspace(request.user)

        rule = get_object_or_404(
            AutomationRule,
            id=rule_id,
            workspace=workspace,
        )

        rule.is_active = not rule.is_active
        rule.save(update_fields=["is_active"])

        return Response({"is_active": rule.is_active})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace

from automation.models import AutomationRule
from .serializers import AutomationRuleSerializer
from django.shortcuts import get_object_or_404


# ---------------------------
# LIST + CREATE
# ---------------------------
class AutomationRuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request):
        workspace = get_user_workspace(request.user)

        rules = AutomationRule.objects.filter(workspace=workspace)
        serializer = AutomationRuleSerializer(rules, many=True)

        return Response(serializer.data)

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

    def get(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        return Response(AutomationRuleSerializer(rule).data)

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

    def delete(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        rule.delete()
        return Response(status=204)


class ToggleAutomationRuleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

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

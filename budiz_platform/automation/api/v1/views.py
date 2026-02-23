from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from automation.engine import process_event
from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace

from drf_spectacular.utils import extend_schema, OpenApiResponse
from common.swagger import workspace_header
from django.db import transaction

from automation.models import AutomationRule
from .serializers import AutomationRuleSerializer, AutomationExecutionLogSerializer
from automation.selectors import get_workspace_logs, get_rule_logs
from django.shortcuts import get_object_or_404
from automation.models import AutomationExecutionLog


# ---------------------------
# LIST + CREATE
# ---------------------------
class AutomationRuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: AutomationRuleSerializer(many=True)},
        description="List all automation rules in the workspace",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
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
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request):
        workspace = get_user_workspace(request.user)

        with transaction.atomic():
            serializer = AutomationRuleSerializer(
                data=request.data,
                context={"workspace": workspace, "user": request.user},
            )
            serializer.is_valid(raise_exception=True)
            rule = serializer.save()
            response_data = AutomationRuleSerializer(rule).data

        return Response(response_data, status=status.HTTP_201_CREATED)


# ---------------------------
# RETRIEVE + UPDATE + DELETE
# ---------------------------
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
        auth=[{"jwtAuth": []}],
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
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        with transaction.atomic():
            serializer = AutomationRuleSerializer(
                rule,
                data=request.data,
                partial=True,
                context={"workspace": rule.workspace},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_data = serializer.data

        return Response(response_data)

    @extend_schema(
        responses={204: OpenApiResponse(description="Automation rule deleted")},
        description="Delete an automation rule",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def delete(self, request, rule_id):
        rule = self.get_object(request, rule_id)
        rule.delete()
        return Response(status=204)


# ---------------------------
# TOGGLE ACTIVE STATUS
# ---------------------------
class ToggleAutomationRuleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Automation rule toggled")},
        description="Toggle automation rule active status",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
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


# ---------------------------
# AUTOMATION LOGS
# ---------------------------
class AutomationLogListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        operation_id="automation_logs_list",
        responses={200: AutomationExecutionLogSerializer(many=True)},
        description="List all automation execution logs in the workspace",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        logs = get_workspace_logs(workspace)
        serializer = AutomationExecutionLogSerializer(logs, many=True)

        return Response(serializer.data)


# ---------------------------
# AUTOMATION RULE LOGS
# ---------------------------
class AutomationRuleLogListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        operation_id="automation_rule_logs_list",
        responses={200: AutomationExecutionLogSerializer(many=True)},
        description="List all execution logs for a specific automation rule",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, rule_id):
        workspace = get_user_workspace(request.user)
        logs = get_rule_logs(workspace, rule_id)
        serializer = AutomationExecutionLogSerializer(logs, many=True)

        return Response(serializer.data)


# ---------------------------
# AUTOMATION LOG DETAIL
# ---------------------------
class AutomationLogDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        responses={200: AutomationExecutionLogSerializer},
        description="Retrieve details of a specific automation execution log",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, log_id):
        workspace = get_user_workspace(request.user)
        log = get_object_or_404(AutomationExecutionLog, id=log_id, workspace=workspace)
        serializer = AutomationExecutionLogSerializer(log)

        return Response(serializer.data)


class RetryAutomationLogAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Automation log retried")},
        description="Retry a failed automation execution log",
        tags=["Automation"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request, log_id):
        workspace = get_user_workspace(request.user)
        log = get_object_or_404(
            AutomationExecutionLog,
            id=log_id,
            workspace=workspace,
            status="failed",
        )

        if log.status != "failed":
            return Response(
                {"detail": "Only failed logs can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = log.payload

        process_event(
            event_name=log.event_type,
            payload=payload,
            workspace=workspace,
            user=request.user,
        )

        # Here you would implement the logic to retry the automation action
        # For example, you might re-queue the action or call the function directly

        return Response({"message": "Retry logic not implemented yet."})

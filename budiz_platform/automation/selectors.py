from .models import AutomationRule, AutomationExecutionLog


def get_active_rules_for_trigger(workspace, event_name):
    return AutomationRule.objects.filter(
        workspace=workspace,
        event_name=event_name,
        is_active=True,
    ).prefetch_related("conditions", "actions")


def get_workspace_logs(workspace):
    return (
        AutomationExecutionLog.objects.filter(workspace=workspace)
        .select_related("rule")
        .order_by("-executed_at")
    )


def get_rule_logs(workspace, rule_id):
    return (
        AutomationExecutionLog.objects.filter(workspace=workspace, rule_id=rule_id)
        .select_related("rule")
        .order_by("-executed_at")
    )

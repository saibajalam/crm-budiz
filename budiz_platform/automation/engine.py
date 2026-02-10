from .rule_matcher import get_matched_rules as match_rules
from .evaluator import evaluate_conditions
from .services.execute_actions import execute_actions
from .models import AutomationExecutionLog
from workspaces.models import Workspace


def process_event(event_name, payload, workspace, user=None):
    rules = match_rules(workspace, event_name, payload)
    for rule in rules:
        if evaluate_conditions(rule.conditions.all(), payload):
            execute_actions(rule.actions.all(), payload, workspace, user)
            # log execution
            AutomationExecutionLog.objects.create(
                workspace=workspace,
                rule=rule,
                object_id=payload.get("id"),
                model_name=payload.get("model"),
                success=True,
                metadata=payload,
            )


def run_engine(workspace_id, event_name, payload, user=None):
    workspace = Workspace.objects.filter(id=workspace_id).first()
    if not workspace:
        return False

    process_event(event_name, payload, workspace, user)
    return True

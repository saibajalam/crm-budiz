import traceback

from workspaces.models import Workspace

from .rule_matcher import get_matched_rules as match_rules
from .evaluator import evaluate_conditions
from .services.execute_actions import execute_actions
from .services.log_service import (
    create_execution_log,
    execute_with_logging,
    already_executed,
)


# -----------------------------------
# HELPERS
# -----------------------------------
def _rule_conditions(rule):
    manager = getattr(rule, "conditions", None)
    if manager is not None:
        return manager.all()
    return rule.automationcondition_set.all()


def _rule_actions(rule):
    manager = getattr(rule, "actions", None)
    if manager is not None:
        return manager.all()
    return rule.automationaction_set.all()


# -----------------------------------
# CORE ENGINE
# -----------------------------------
def process_event(event_name, payload, workspace, user=None):
    """
    Main automation processor.
    Called when any CRM event happens.
    """

    rules = match_rules(workspace, event_name, payload)

    if not rules:
        return

    for rule in rules:
        try:
            # -----------------------------------
            # IDEMPOTENCY KEY
            # -----------------------------------
            key = f"{event_name}:{rule.id}:{payload.get('id')}"

            if already_executed(key):
                continue

            # -----------------------------------
            # CONDITION CHECK
            # -----------------------------------
            conditions = _rule_conditions(rule)
            if not evaluate_conditions(conditions, payload):
                continue

            # -----------------------------------
            # EXECUTE ACTIONS WITH LOGGING
            # -----------------------------------
            execute_with_logging(
                workspace=workspace,
                rule=rule,
                event_type=event_name,
                payload=payload,
                target_object_id=payload.get("id"),
                target_model=payload.get("model"),
                idempotency_key=key,
                action_type="rule_execution",
                func=lambda: execute_actions(
                    _rule_actions(rule),
                    payload,
                    workspace,
                    user,
                ),
            )

        except Exception as e:
            # -----------------------------------
            # HARD FAIL LOG
            # -----------------------------------
            create_execution_log(
                workspace=workspace,
                rule=rule,
                event_type=event_name,
                payload=payload,
                target_object_id=payload.get("id"),
                target_model=payload.get("model"),
                status="failed",
                error_message=str(e),
                error_trace=traceback.format_exc(),
            )


# -----------------------------------
# ENTRYPOINT
# -----------------------------------
def run_engine(workspace_id, event_name, payload, user=None):
    """
    Entry point from services.
    """

    workspace = Workspace.objects.filter(id=workspace_id).first()
    if not workspace:
        return False

    process_event(event_name, payload, workspace, user)
    return True

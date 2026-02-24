import traceback

from workspaces.models import Workspace

from .rule_matcher import get_matched_rules as match_rules
from .services.evaluator import evaluate_conditions
from .services.execute_actions import execute_actions

from .services.log_service import (
    create_execution_log,
    execute_with_logging,
    already_executed,
)

# analytics integration
from analytics.services.automation_analytics_service import (
    update_automation_metrics,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _rule_conditions(rule):
    """
    Safe accessor for rule conditions.
    Supports related_name or default reverse manager.
    """
    manager = getattr(rule, "conditions", None)
    if manager is not None:
        return manager.all()
    return rule.conditions.all()


def _rule_actions(rule):
    """
    Safe accessor for rule actions.
    """
    manager = getattr(rule, "actions", None)
    if manager is not None:
        return manager.all()
    return rule.actions.all()


# ============================================================
# CORE ENGINE
# ============================================================


def process_event(event_name: str, payload: dict, workspace, user=None):
    """
    Main automation processor.

    Guarantees:
    - Exactly ONE AutomationExecutionLog per matched rule
    - Logs for skipped / success / failed cases
    """

    rules = match_rules(workspace, event_name, payload)

    if not rules:
        return

    for rule in rules:

        key = f"{event_name}:{rule.id}:{payload.get('target_object_id')}"
        target_object_id = payload.get("target_object_id")
        target_model = payload.get("target_model")

        status = "skipped"
        error_message = ""
        error_trace = ""

        try:
            # -----------------------------------
            # IDEMPOTENCY CHECK
            # -----------------------------------
            if already_executed(key):
                status = "skipped"

            else:
                # -----------------------------------
                # CONDITION EVALUATION
                # -----------------------------------
                conditions = _rule_conditions(rule)

                if not evaluate_conditions(conditions, payload):
                    status = "skipped"

                else:
                    # -----------------------------------
                    # ACTIONS
                    # -----------------------------------
                    actions = _rule_actions(rule)

                    if not actions.exists():
                        status = "skipped"

                    else:
                        # -----------------------------------
                        # EXECUTE ACTIONS
                        # -----------------------------------
                        try:
                            execute_actions(
                                actions,
                                payload,
                                workspace,
                                user,
                            )

                            update_automation_metrics(workspace, success=True)
                            status = "success"

                        except Exception as action_error:
                            update_automation_metrics(workspace, success=False)
                            status = "failed"
                            error_message = str(action_error)
                            error_trace = traceback.format_exc()

        except Exception as e:
            # Hard failure (rule crash / evaluation crash)
            status = "failed"
            error_message = str(e)
            error_trace = traceback.format_exc()

        # -----------------------------------
        # 🔒 SINGLE GUARANTEED LOG PER RULE
        # -----------------------------------
        try:
            create_execution_log(
                workspace=workspace,
                rule=rule,
                event_type=event_name,
                payload=payload,
                target_object_id=target_object_id,
                target_model=target_model,
                idempotency_key=key,
                action_type="rule_execution",
                status=status,
                error_message=error_message,
                error_trace=error_trace,
            )
        except Exception as log_error:
            # Logging should NEVER break the processor
            print(
                f"[Automation] Failed to write execution log for rule {rule.id}: {log_error}"
            )

        print(f"Rule {rule.id} processed: {status}")


# ============================================================
# ENTRYPOINT FROM SERVICES
# ============================================================


def run_engine(workspace_id: int, event_name: str, payload: dict, user=None):
    """
    Entry point called from:
    - lead_service
    - deal_service
    - future events

    Safe workspace resolver.
    """

    workspace = Workspace.objects.filter(id=workspace_id).first()
    if not workspace:
        return False

    process_event(event_name, payload, workspace, user)
    return True

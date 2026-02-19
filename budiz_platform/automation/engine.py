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
    return rule.automationcondition_set.all()


def _rule_actions(rule):
    """
    Safe accessor for rule actions.
    """
    manager = getattr(rule, "actions", None)
    if manager is not None:
        return manager.all()
    return rule.automationaction_set.all()


# ============================================================
# CORE ENGINE
# ============================================================


def process_event(event_name: str, payload: dict, workspace, user=None):
    """
    Main automation processor.

    Flow:
    1. Fetch matching rules
    2. Idempotency check
    3. Evaluate conditions
    4. Execute actions
    5. Log + analytics
    """

    rules = match_rules(workspace, event_name, payload)

    if not rules:
        return

    for rule in rules:
        try:
            # -----------------------------------
            # IDEMPOTENCY KEY
            # prevents duplicate execution
            # -----------------------------------
            key = f"{event_name}:{rule.id}:{payload.get('id')}"

            if already_executed(key):
                continue

            # -----------------------------------
            # CONDITION EVALUATION
            # -----------------------------------
            conditions = _rule_conditions(rule)

            if not evaluate_conditions(conditions, payload):
                continue

            # -----------------------------------
            # EXECUTE ACTIONS (with logging wrapper)
            # -----------------------------------
            try:
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

                # -----------------------------------
                # SUCCESS ANALYTICS
                # -----------------------------------
                update_automation_metrics(workspace, success=True)

            except Exception as action_error:
                # -----------------------------------
                # FAILURE ANALYTICS
                # -----------------------------------
                update_automation_metrics(workspace, success=False)

                # Re-raise so logging wrapper handles it
                raise action_error

        except Exception as e:
            # -----------------------------------
            # HARD FAILURE LOG
            # (rule crash, evaluation crash, etc.)
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

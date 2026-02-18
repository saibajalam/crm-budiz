import time
import traceback
from typing import Optional

from django.db import transaction
from django.utils import timezone

from automation.models import AutomationExecutionLog


# =====================================================
# CREATE LOG
# =====================================================
@transaction.atomic
def create_execution_log(
    *,
    workspace,
    rule=None,
    event_type: str,
    target_object_id: Optional[int] = None,
    target_model: Optional[str] = None,
    action_type: Optional[str] = None,
    payload: dict | None = None,
    metadata: dict | None = None,
    idempotency_key: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    error_trace: Optional[str] = None,
    duration_ms: Optional[int] = None,
):
    """
    Create a single automation execution log.
    """

    log = AutomationExecutionLog.objects.create(
        workspace=workspace,
        rule=rule,
        event_type=event_type,
        target_object_id=target_object_id,
        target_model=target_model,
        action_type=action_type,
        payload=payload or {},
        metadata=metadata or {},
        idempotency_key=idempotency_key,
        status=status,
        error_message=error_message,
        error_trace=error_trace,
        duration_ms=duration_ms,
        executed_at=timezone.now(),
    )

    return log


# =====================================================
# SAFE EXECUTION WRAPPER
# =====================================================
def execute_with_logging(
    *,
    workspace,
    rule,
    event_type: str,
    action_type: str,
    payload: dict,
    target_object_id=None,
    target_model=None,
    idempotency_key=None,
    func,
):
    """
    Wrap any automation action with logging + timing.
    """

    start = time.time()

    try:
        result = func()

        duration = int((time.time() - start) * 1000)

        create_execution_log(
            workspace=workspace,
            rule=rule,
            event_type=event_type,
            action_type=action_type,
            payload=payload,
            target_object_id=target_object_id,
            target_model=target_model,
            idempotency_key=idempotency_key,
            status="success",
            duration_ms=duration,
        )

        return result

    except Exception as e:
        duration = int((time.time() - start) * 1000)

        create_execution_log(
            workspace=workspace,
            rule=rule,
            event_type=event_type,
            action_type=action_type,
            payload=payload,
            target_object_id=target_object_id,
            target_model=target_model,
            idempotency_key=idempotency_key,
            status="failed",
            error_message=str(e),
            error_trace=traceback.format_exc(),
            duration_ms=duration,
        )

        raise


# =====================================================
# IDEMPOTENCY CHECK
# =====================================================
def already_executed(idempotency_key):
    if not idempotency_key:
        return False

    return AutomationExecutionLog.objects.filter(
        idempotency_key=idempotency_key,
        status="success",
    ).exists()

from tasks.models import Task


def execute(payload, params, workspace, user):
    """
    Create a task placeholder.
    params = {"title": "Follow up", "description": "...", "due_at": "...", "status": "open", "assigned_to_id": 1, "priority": "high", "completed_at": "..."}
    """
    title = params.get("title")

    if not title:
        return False

    task = Task.objects.create(
        workspace=workspace,
        title=title,
        description=params.get("description", ""),
        status=params.get("status", "open"),
        due_at=params.get("due_at"),
        assigned_to_id=params.get("assigned_to_id"),
        priority=params.get("priority"),
        created_by=user,
        related_object_id=payload.get("target_object_id"),
        related_to_type=payload.get("target_model"),
        completed_at=params.get("completed_at"),
    )

    return bool(task)

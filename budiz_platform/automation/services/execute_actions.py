from ..actions import update, assign, emails, create_task, webhook

ACTION_MAP = {
    "update_field": update.execute,
    "assign_user": assign.execute,
    "send_email": emails.execute,
    "create_task": create_task.execute,
    "webhook": webhook.execute,
}


def execute_actions(actions, payload, workspace, user):
    """
    Execute actions for a matched rule.
    """
    results = []
    for action in actions:
        executor = ACTION_MAP.get(action.action_type)
        if executor:
            result = executor(payload, action.config, workspace, user)
            results.append(result)
    return results

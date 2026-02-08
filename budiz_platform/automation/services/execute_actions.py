from ..actions import update, assign, emails

ACTION_MAP = {
    "update_field": update.execute,
    "assign_user": assign.execute,
    "send_email": emails.execute,
}


def execute_actions(actions, payload, workspace, user):
    """
    Execute actions for a matched rule.
    """
    results = []
    for action in actions:
        executor = ACTION_MAP.get(action.action_type)
        if executor:
            result = executor(payload, action.params, workspace, user)
            results.append(result)
    return results

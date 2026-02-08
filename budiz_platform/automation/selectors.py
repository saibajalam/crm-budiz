from .models import AutomationRule


def get_active_rules_for_trigger(workspace, trigger):
    return AutomationRule.objects.filter(
        workspace=workspace,
        trigger=trigger,
        is_active=True,
    ).prefetch_related("conditions", "actions")

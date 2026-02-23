from automation.selectors import get_active_rules_for_trigger


def get_matched_rules(workspace, trigger, instance):
    rules = get_active_rules_for_trigger(workspace, trigger)
    return list(rules)

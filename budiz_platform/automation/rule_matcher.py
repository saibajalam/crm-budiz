from automation.selectors import get_active_rules_for_trigger
from automation.evaluator import evaluate_conditions


def get_matched_rules(workspace, trigger, instance):
    rules = get_active_rules_for_trigger(workspace, trigger)

    matched = []

    for rule in rules:
        if evaluate_conditions(instance, rule.conditions.all()):
            matched.append(rule)

    return matched

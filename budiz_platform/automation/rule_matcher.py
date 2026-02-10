from django.forms.models import model_to_dict

from automation.selectors import get_active_rules_for_trigger
from automation.evaluator import evaluate_conditions


def _build_payload(instance):
    if isinstance(instance, dict):
        return instance

    try:
        return model_to_dict(instance)
    except Exception:
        return {}


def get_matched_rules(workspace, trigger, instance):
    rules = get_active_rules_for_trigger(workspace, trigger)

    matched = []
    payload = _build_payload(instance)

    for rule in rules:
        if evaluate_conditions(rule.conditions.all(), payload):
            matched.append(rule)

    return matched

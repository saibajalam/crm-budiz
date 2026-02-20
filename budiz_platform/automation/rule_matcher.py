from django.forms.models import model_to_dict

from automation.selectors import get_active_rules_for_trigger
from automation.services.evaluator import evaluate_conditions


def _rule_conditions(rule):
    manager = getattr(rule, "conditions", None)
    if manager is not None:
        return manager.all()
    legacy_manager = getattr(rule, "conditions", None)
    if legacy_manager is not None:
        return legacy_manager.all()
    return rule.conditions.all()


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
        if evaluate_conditions(_rule_conditions(rule), payload):
            matched.append(rule)

    return matched

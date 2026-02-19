from ..constants import OPERATORS


def evaluate_conditions(conditions, payload):
    """
    conditions: list of AutomationCondition objects
    payload: dict of event data
    """
    for cond in conditions:
        field_value = payload.get(cond.field)
        if field_value is None:
            return False
        op_func = OPERATORS.get(cond.operator)
        if not op_func:
            return False
        if not op_func(field_value, cond.value):
            return False
    return True

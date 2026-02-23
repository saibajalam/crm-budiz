# Define triggers, actions, operators
TRIGGERS = [
    "lead.created",
    "lead.status_changed",
    "deal.created",
    "deal.won",
    "deal.stage_changed",
    "task.completed",
]

ACTION_CHOICES = [
    ("assign_user", "Assign User"),
    ("send_email", "Send Email"),
    ("create_task", "Create Task"),
    ("webhook", "Webhook"),
    ("update_field", "Update Field"),
    ("rule_execution", "Rule Execution"),
]

OPERATORS = {
    "equals": lambda a, b: a == b,
    "not_equals": lambda a, b: a != b,
    "contains": lambda a, b: b in a,
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
}

from ..utils import get_round_robin_user
from django.contrib.auth import get_user_model

User = get_user_model()


def assign_lead_from_form(*, form, lead):
    if not hasattr(form, "assignment_type"):
        return

    assignee = None

    if form.assignment_type == "fixed" and form.fixed_assignee:
        assignee = form.fixed_assignee

    elif form.assignment_type == "round_robin":
        assignee = get_round_robin_user(form)

    if assignee:
        lead.assigned_to = assignee
        lead.save(update_fields=["assigned_to"])


def update_form_assignment(*, form, data):
    form.assignment_type = data["assignment_type"]

    if data["assignment_type"] == "fixed":
        user = User.objects.get(id=data["fixed_assignee_id"])
        form.fixed_assignee = user

    elif data["assignment_type"] == "round_robin":
        users = User.objects.filter(id__in=data["round_robin_user_ids"])
        form.round_robin_users.set(users)

    form.save()

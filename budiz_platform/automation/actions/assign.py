def execute(payload, params, workspace, user):
    """
    Assign Lead/Deal to a user
    params = {"user_id": 5}
    """
    model = payload.get("model")
    obj_id = payload.get("id")
    user_id = params.get("user_id")

    from django.contrib.auth import get_user_model

    User = get_user_model()

    assignee = User.objects.filter(id=user_id).first()
    if not assignee:
        return False

    if model == "Lead":
        from leads.models import Lead

        obj = Lead.objects.filter(id=obj_id, workspace=workspace).first()
        if obj:
            obj.assigned_to = assignee
            obj.save(update_fields=["assigned_to"])
            return True
    elif model == "Deal":
        from deals.models import Deal

        obj = Deal.objects.filter(id=obj_id, workspace=workspace).first()
        if obj:
            obj.assigned_to = assignee
            obj.save(update_fields=["assigned_to"])
            return True
    return False

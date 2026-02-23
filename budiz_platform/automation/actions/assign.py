def execute(payload, params, workspace, user):
    """
    Assign Lead/Deal to a user
    params = {"user_id": 5}
    """
    target_model = payload.get("target_model")
    target_object_id = payload.get("target_object_id")
    user_id = params.get("user_id")

    from django.contrib.auth import get_user_model

    User = get_user_model()

    assignee = User.objects.filter(id=user_id).first()
    if not assignee:
        return False

    if target_model == "Lead":
        from leads.models import Lead

        obj = Lead.objects.filter(id=target_object_id, workspace=workspace).first()
        if obj:
            obj.assigned_to = assignee
            obj.save(update_fields=["assigned_to"])
            return True
    elif target_model == "Deal":
        from deals.models import Deal

        obj = Deal.objects.filter(id=target_object_id, workspace=workspace).first()
        if obj:
            obj.assigned_to = assignee
            obj.save(update_fields=["assigned_to"])
            return True
    return False

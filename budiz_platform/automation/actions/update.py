def execute(payload, params, workspace, user):
    """
    Update fields on Lead or Deal
    params = {"field": "status", "value": "contacted"}
    """
    target_model = payload.get("target_model")
    target_object_id = payload.get("target_object_id")

    if target_model == "Lead":
        from leads.models import Lead

        obj = Lead.objects.filter(id=target_object_id, workspace=workspace).first()
    elif target_model == "Deal":
        from deals.models import Deal

        obj = Deal.objects.filter(id=target_object_id, workspace=workspace).first()
    else:
        return False

    if not obj:
        return False

    setattr(obj, params.get("field"), params.get("value"))
    obj.save(update_fields=[params.get("field")])
    return True

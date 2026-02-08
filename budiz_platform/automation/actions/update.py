def execute(payload, params, workspace, user):
    """
    Update fields on Lead or Deal
    params = {"field": "status", "value": "contacted"}
    """
    model = payload.get("model")
    obj_id = payload.get("id")

    if model == "Lead":
        from leads.models import Lead

        obj = Lead.objects.filter(id=obj_id, workspace=workspace).first()
    elif model == "Deal":
        from deals.models import Deal

        obj = Deal.objects.filter(id=obj_id, workspace=workspace).first()
    else:
        return False

    if not obj:
        return False

    setattr(obj, params.get("field"), params.get("value"))
    obj.save(update_fields=[params.get("field")])
    return True

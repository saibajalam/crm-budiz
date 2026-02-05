def get_round_robin_user(form):
    users = list(
        form.round_robin_users.filter(
            workspace_members__workspace=form.workspace,
            workspace_members__is_active=True,
        ).distinct()
    )

    if not users:
        return None

    index = form.round_robin_index % len(users)
    user = users[index]

    form.round_robin_index = (index + 1) % len(users)
    form.save(update_fields=["round_robin_index"])

    return user

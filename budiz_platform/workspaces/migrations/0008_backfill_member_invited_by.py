from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workspaces", "0007_delete_workspacecounter"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE workspace_member wm
                SET invited_by_id = wi.invited_by_id
                FROM workspace_invite wi
                JOIN users u ON u.email = wi.email
                WHERE wm.workspace_id = wi.workspace_id
                  AND wm.user_id = u.id
                  AND wi.is_accepted = TRUE
                  AND wi.invited_by_id IS NOT NULL
                  AND wm.invited_by_id IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

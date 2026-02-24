from django.db import migrations


def create_leads_table_if_missing(apps, schema_editor):
    existing_tables = schema_editor.connection.introspection.table_names()
    if "leads" in existing_tables:
        return

    Lead = apps.get_model("leads", "Lead")
    schema_editor.create_model(Lead)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0023_lead_leads_is_conv_124d7f_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(create_leads_table_if_missing, noop_reverse),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0001_initial"),
        ("deals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DealContact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(blank=True, default="", max_length=100)),
                ("is_primary", models.BooleanField(default=False)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_deals",
                        to="contact.contact",
                    ),
                ),
                (
                    "deal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deal_contacts",
                        to="deals.deal",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deal_contacts",
                        to="workspaces.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "deal_contact",
                "unique_together": {("deal", "contact")},
            },
        ),
        migrations.AddIndex(
            model_name="dealcontact",
            index=models.Index(
                fields=["workspace", "deal"],
                name="deal_contac_workspa_016f2c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="dealcontact",
            index=models.Index(
                fields=["workspace", "contact"],
                name="deal_contac_workspa_ff7438_idx",
            ),
        ),
    ]

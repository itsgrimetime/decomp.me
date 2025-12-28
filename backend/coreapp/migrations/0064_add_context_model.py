# Generated manually for issue #1739 - Deduplicate Scratch.context

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coreapp", "0063_apply_default_flags_to_dc_scratches"),
    ]

    operations = [
        migrations.CreateModel(
            name="Context",
            fields=[
                (
                    "hash",
                    models.CharField(max_length=64, primary_key=True, serialize=False),
                ),
                ("data", models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name="scratch",
            name="context_obj",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="coreapp.context",
            ),
        ),
    ]

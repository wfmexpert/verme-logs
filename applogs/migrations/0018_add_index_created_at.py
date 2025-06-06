# Generated by Django 3.2.25 on 2025-04-17 15:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("applogs", "0017_JSONField_fix"),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS applogs_serverrecord__created_at__idx1 ON applogs_serverrecord (created_at)",
            reverse_sql="DROP INDEX IF EXISTS applogs_serverrecord__created_at__idx1",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS applogs_clientrecord__created_at__idx1 ON applogs_clientrecord (created_at)",
            reverse_sql="DROP INDEX IF EXISTS  applogs_clientrecord__created_at__idx1",
        ),
    ]

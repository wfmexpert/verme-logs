# Generated by Django 2.2.2 on 2020-11-26 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applogs', '0015_add_user_and_headers'),
    ]

    operations = [
        migrations.AddField(
            model_name='serverrecord',
            name='request',
            field=models.TextField(blank=True, null=True, verbose_name='текст запроса'),
        ),
    ]
# Generated by Django 2.0.9 on 2018-12-06 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xlsexport', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='exporttemplate',
            name='default',
            field=models.BooleanField(default=False, verbose_name='по умолчанию'),
        ),
    ]

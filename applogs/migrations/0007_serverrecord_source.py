# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-08-16 09:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applogs', '0006_auto_20180815_1747'),
    ]

    operations = [
        migrations.AddField(
            model_name='serverrecord',
            name='source',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='источник'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-06 18:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('applogs', '0003_auto_20170530_2129'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clientrecord',
            options={'verbose_name': 'Системная ошибки', 'verbose_name_plural': 'Системные ошибки'},
        ),
        migrations.AlterModelOptions(
            name='serverrecord',
            options={'verbose_name': 'Журнал работы служб', 'verbose_name_plural': 'Журнал работы служб'},
        ),
    ]

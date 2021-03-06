# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-08-15 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applogs', '0005_level_and_params_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='serverrecord',
            name='headquater',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='клиент'),
        ),
        migrations.AddField(
            model_name='serverrecord',
            name='tags',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='теги'),
        ),
        migrations.AlterField(
            model_name='serverrecord',
            name='level',
            field=models.CharField(choices=[('info', 'INFO'), ('error', 'ERROR'), ('debug', 'DEBUG')], default='info', max_length=5, verbose_name='важность'),
        ),
    ]

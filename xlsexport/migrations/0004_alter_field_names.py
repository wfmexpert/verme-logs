# Generated by Django 2.0.5 on 2018-12-25 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('xlsexport', '0003_importtemplate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exporttemplate',
            options={'verbose_name': 'Шаблоны импорта / экспорта в Excel', 'verbose_name_plural': 'Шаблоны импорта / экспорта в Excel'},
        ),
        migrations.AlterModelOptions(
            name='importtemplate',
            options={'verbose_name': 'Импорт из Excel', 'verbose_name_plural': 'Импорт из Excel'},
        ),
    ]

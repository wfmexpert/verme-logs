from django.db import migrations, models


temp1 = {
    "name": "Параметры орг. единиц",
    "code": "unitparam",
    "format": "xlsx",
    "model": "labour.unitparam",
    "params": {
        "fields": [
            {
                "name": "Код параметра",
                "field": "param.code",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Орг. единица (тип)",
                "field": "unit_type.id",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Орг. единица",
                "field": "unit.code",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Дата начала",
                "field": "start_date",
                "width": 15,
                "format": "%d.%m.%Y",
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Дата конца",
                "field": "end_date",
                "width": 15,
                "format": "%d.%m.%Y",
                "key_field": False,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Значение",
                "field": "value",
                "width": 15,
                "format": "0.000",
                "key_field": False,
                "export_ignore": False,
                "import_ignore": False
            }
        ],
        "filename": "unitparam"
    }
}
temp2 = {
    "name": "Характеристики орг. единиц",
    "code": "unitfeature",
    "format": "xlsx",
    "model": "features.unitfeature",
    "params": {
        "fields": [
            {
                "name": "Орг.единица (тип)",
                "field": "unit_type.id",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Орг.единица",
                "field": "unit.code",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Характеристика",
                "field": "feature_value.feature.code",
                "width": 15,
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Значение",
                "field": "feature_value.code",
                "width": 15,
                "key_field": False,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Действует с",
                "field": "start_date",
                "width": 15,
                "format": "%d.%m.%Y",
                "key_field": True,
                "export_ignore": False,
                "import_ignore": False
            },
            {
                "name": "Действует до",
                "field": "end_date",
                "width": 15,
                "format": "%d.%m.%Y",
                "key_field": False,
                "export_ignore": False,
                "import_ignore": False
            }
        ],
        "filename": "unitfeature"
    }
}
temp_list = (temp1, temp2)


def get_param(temps=temp_list, model='xlsexport.ExportTemplate'):
    return temps, model


def create_temp(apps, schema_editor):
    temps, model_name = get_param()
    obj = apps.get_model(model_name)
    for i in temps:
        if not obj.objects.filter(code=i['code']).exists():
            t = obj.objects.create(**i)


def undo(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('xlsexport', '0004_alter_field_names'),
    ]

    operations = [
        migrations.RunPython(create_temp, undo),

    ]



from django.apps import apps
from django.http import JsonResponse
from .models import ExportTemplate


def get_report_by_code(code=None, queryset=None):
    """
    Возвращает сформированный отчет по его коду
    """
    if not code:
        return None

    template = ExportTemplate.objects.filter(code=code).first()
    if not template:
        return JsonResponse({"non_field_errors": f"Отчет с кодом '{code}' не найден. Для экспорта в Excel необходимо создать шаблон отчета."}, status=400)
    return template.to_export(queryset)


def get_report_by_model(model=None, queryset=None):
    """
    Возвращает сформированный отчет по модели
    Если отчета нет, то формирует шаблон по умолчанию
    """
    if not model:
        return None

    template = ExportTemplate.objects.filter(model=model).order_by('default').first()
    if not template:
        # Получаем поля модели
        model_obj = apps.get_model(*(model.split('.', 1)))
        fields = model_obj._meta.get_fields()
        filename = model.split('.')[1]
        params = {"fields": [],
                  "filename": filename}

        for field in fields:
            field_dict = {"name": field.verbose_name, "field": field.name, "width": 15}
            if field.get_internal_type() == 'DateTimeField':
                field_dict.update({"format": "%d.%m.%y %H:%M:%S"})
            if field.get_internal_type() == 'FloatField':
                field_dict.update({"format": "0.000"})
            params['fields'].append(field_dict)

        template_dict = {"code": filename,
                         "name": f'Список объектов {filename}',
                         "model": model,
                         "params": params,
                         "default": True}

        # Создаем шаблон отчета
        template = ExportTemplate.objects.create(template_dict)
    return template.to_export(queryset)


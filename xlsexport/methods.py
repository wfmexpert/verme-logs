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
        return JsonResponse({"non_field_errors": "Не найден отчет с указанным кодом"}, status=400)
    return template.to_export(queryset)

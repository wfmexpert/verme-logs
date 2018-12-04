from .models import ExportTemplate


def get_report_by_code(code=None):
    """
    Возвращает сформированный отчет по его коду
    """
    print("CODE", code)

    if not code:
        return None

    template = ExportTemplate.objects.filter(code=code).first()
    print("TEMPLATE", template)
    if not template:
        return None

    return template.to_export()

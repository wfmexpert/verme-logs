from django.contrib.admin import *
from .methods import get_report_by_code, get_report_by_model


class AdminExportMixin(ModelAdmin):
    actions = ('xls_export',)

    def xls_export(self, request, queryset):
        return get_report_by_model(str(self.model._meta), queryset)
    xls_export.short_description = 'Выгрузить в Excel'

    class Meta:
        abstract = True

from django.contrib import admin
from .models import ExportTemplate
from .forms import ExportTemplateForm


@admin.register(ExportTemplate)
class ExportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'model', 'format')
    list_filter = ('format',)
    search_fields = ('name', 'code')
    form = ExportTemplateForm

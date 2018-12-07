from django.contrib import admin
from .models import ExportTemplate, ImportTemplate
from .forms import ExportTemplateForm, ImportTemplateForm

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe


@staff_member_required
def xls_export_view(request):
    if request.method == 'POST':
        export_template = ExportTemplate.objects.filter(id=request.POST['export_template_id']).first()
        if not export_template:
            messages.error(request, "Шаблон отчета не найден.")
        export_template.to_export()
    redirect_url = request.META.get('HTTP_REFERER', reverse('admin:xlsexport_exporttemplate_changelist'))
    return HttpResponseRedirect(redirect_url)

@admin.register(ExportTemplate)
class ExportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'model', 'format')
    list_filter = ('format',)
    search_fields = ('name', 'code')
    form = ExportTemplateForm
    actions = ('run_export', )

    def run_export(self, request, queryset):
        return queryset.first().to_export()
    run_export.short_description = 'Запустить экспорт в Excel'

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        if request.POST:
            form = ImportTemplateForm(request.POST, request.FILES)
            if form.is_valid():
                template = form.cleaned_data.get('template')
                file = form.cleaned_data.get('file')
                errors = template.to_import(file)
                if errors:
                    msg = ''.join(['Строка: {} ошибка:{}<br/>'.format(error['rownum'], error['exc'])
                                   for error in errors])
                    msg = mark_safe(msg)
                    messages.add_message(request, messages.ERROR, msg)
                form = ImportTemplateForm()
        else:
            form = ImportTemplateForm()

        response.context_data['form'] = form

        return response

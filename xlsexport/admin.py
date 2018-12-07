from django.contrib import admin
from .models import ExportTemplate, ImportTemplate
from .forms import ExportTemplateForm, ImportTemplateForm

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http.response import HttpResponseRedirect
from django.urls import reverse


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
    change_list_template = 'admin/importtemplate/change_list.html'

    def _save_file(self, file, path):
        with open(path, 'wb+') as fixture:
            for chunk in file.chunks():
                fixture.write(chunk)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        if request.POST:
            form = ImportTemplateForm(request.POST, request.FILES)
            if form.is_valid():
                template = form.cleaned_data.get('template')
                file = form.cleaned_data.get('file')
                print ("TEMPALTE", template)
                #filename = '{0}.json'.format(uuid.uuid4())
                #temp_dir = '/tmp'
                #new_file_path = os.path.join(temp_dir, filename)
                #self._save_file(file, new_file_path)
                #call_command('loaddata', new_file_path)
                #os.remove(new_file_path)

                response.context_data['success_message'] = """Данные из файла загружены в базу"""
                form = ImportTemplateForm()
        else:
            form = ImportTemplateForm()

        response.context_data['form'] = form

        return response

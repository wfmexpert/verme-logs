from django.contrib import admin
from .models import ExportTemplate
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

@admin.register()
class ImportTemplateAdmin(admin.ModelAdmin):
    change_list_template = 'admin/importtemplate/change_list.html'

    def _save_file(self, file, path):
        with open(path, 'wb+') as fixture:
            for chunk in file.chunks():
                fixture.write(chunk)

    def _build_output_file_path(self, filename, num, output_path):
        names = filename.split('.')
        names[0] += str(num)
        temp_filename = '.'.join(names)
        return os.path.join(output_path, temp_filename)

    def _build_output_path(self, filename, temp_dir):
        names = filename.split('.')
        output_folder = '.'.join(names[:-1])
        output_path = os.path.join(temp_dir, output_folder)
        os.makedirs(output_path, exist_ok=True)
        return output_path

    def _make_http_response(self, path):
        with open(path, 'rb') as file:
            response = HttpResponse(
                file.read(),
                content_type="application/json"
            )
        subprocess.Popen("rm {0}".format(path), shell=True)
        response['Content-Disposition'] = "attachment; filename=fixtures.json"
        return response

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        if request.POST:
            form = CopySettingsForm(request.POST, request.FILES)
            if form.is_valid():
                packages = form.cleaned_data.get('packages')
                file = form.cleaned_data.get('file')
                filename = '{0}.json'.format(uuid.uuid4())
                temp_dir = '/tmp'
                new_file_path = os.path.join(temp_dir, filename)
                if request.POST.get('load'):
                    self._save_file(file, new_file_path)
                    call_command('loaddata', new_file_path)
                    os.remove(new_file_path)

                    response.context_data['success_message'] = """
                        Данные из фикстур загружены в базу"""
                else:
                    output_path = self._build_output_path(filename, temp_dir)
                    for num, package in enumerate(packages):
                        output_file_path = self._build_output_file_path(
                            filename, num, output_path)
                        call_command(
                            'dumpdata', package, indent=2,
                            output=output_file_path, natural_foreign=True
                        )
                    merge_json_files(output_path, new_file_path)
                    return self._make_http_response(new_file_path)

                form = CopySettingsForm()
        else:
            form = CopySettingsForm()

        response.context_data['form'] = form

        return response

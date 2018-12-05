import xlwt

from datetime import timedelta
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import StreamingHttpResponse
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.timezone import make_naive

from .forms import ServerRecordForm
from .models import ClientRecord, ServerRecord
from .utils import XLSWriterUtil
from xlsexport.methods import get_report_by_code

@staff_member_required
def delete_all_client_records_view(request):
    if request.method == 'POST':
        ClientRecord.objects.all().delete()
    return HttpResponseRedirect(reverse('admin:applogs_clientrecord_changelist'))


@admin.register(ClientRecord)
class ClientRecordAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user_agent', 'html_message')
    search_fields = ('message',)

    def html_message(self, obj):
        return format_html('<pre>{}</pre>', obj.message[:200])

    def has_add_permission(self, request):
        return False


@staff_member_required
def delete_old_server_records_view(request):
    if request.method == 'POST':
        ServerRecord.objects.filter(created_at__lt=(timezone.now() - timedelta(days=90))).delete()
    return HttpResponseRedirect(reverse('admin:applogs_serverrecord_changelist'))


class ServerRecordXLS(XLSWriterUtil):
    def __init__(self, queryset):
        super().__init__()
        self.queryset = queryset

    def generate(self):
        self.wb = xlwt.Workbook(encoding='utf-8', style_compression=2)
        self.ws = self.wb.add_sheet('report')

        self.col(0).width = self.get_width_for_col(15)
        self.col(6).width = self.get_width_for_col(64)

        with self.add_style({'font': 'bold on'}):
            for c, col_name in enumerate(['ДАТА СОЗДАНИЯ', 'КЛИЕНТ', 'ИСТОЧНИК', 'МЕТОД', 'ВАЖНОСТЬ', 'ПРОДОЛЖИТЕЛЬНОСТЬ', 'ОПИСАНИЕ']):
                self.write(0, c, col_name)

        with self.add_position(1, 0):
            for r, record in enumerate(self.queryset):
                # без `replace(tzinfo=None)` будет `can't subtract offset-naive and offset-aware datetimes`
                self.write(r, 0, make_naive(record.created_at), {'num_format_str': 'DD.MM.YYYY hh:mm:ss'})
                self.write(r, 1, record.headquater)
                self.write(r, 2, record.source)
                self.write(r, 3, record.method)
                self.write(r, 4, record.level)
                self.write(r, 5, record.duration, {'num_format_str': '0.000'})
                self.write(r, 6, record.message)


@admin.register(ServerRecord)
class ServerRecordAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'headquater', 'source', 'method', 'level', 'duration_rounded', 'html_message')
    list_filter = ('source', 'method', 'level', 'headquater')
    search_fields = ('message', 'tags')
    actions = ('make_report',)
    form = ServerRecordForm

    def html_message(self, obj):
        return format_html('<pre>{}</pre>', obj.message[:200])
    html_message.short_description = 'Описание'

    def make_report(self, request, queryset):
        return get_report_by_code('serverrecord', queryset)
        #content = ServerRecordXLS(queryset[:65000]).generate_as_buffer()
        #response = StreamingHttpResponse(content, content_type='application/vnd.ms-excel')
        #today = make_naive(timezone.now()).strftime('%Y%m%d.%H%M%S')
        #filename = 'serverrecord.%s.xls' % today
        #response["Content-Disposition"] = f"attachment; filename*=UTF-8''{urlquote(filename)}"
        #return response
    make_report.short_description = 'Выгрузить в Excel'

    def duration_rounded(self, obj):
        return round(obj.duration, 3)
    duration_rounded.short_description = "Продолжительность"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

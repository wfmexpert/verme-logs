import xlwt

from datetime import timedelta
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
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
from xlsexport.mixins import AdminExportMixin

from django.db.models import Q

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


class SourceFilter(admin.SimpleListFilter):
    title = 'Источник'
    parameter_name = 'source'

    def lookups(self, request, model_admin):
        def custom_sql():
            query = """WITH RECURSIVE t AS (
                    (SELECT source FROM applogs_serverrecord ORDER BY source LIMIT 1) UNION ALL
                    SELECT (SELECT source FROM applogs_serverrecord WHERE source > t.source ORDER BY source LIMIT 1)
                    FROM t WHERE t.source IS NOT NULL ) SELECT source FROM t WHERE source IS NOT NULL;"""
            with connections['applogs'].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return rows
        return [(row[0], row[0]) for row in custom_sql()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(Q(source=self.value()))


class MethodFilter(admin.SimpleListFilter):
    title = 'Метод'
    parameter_name = 'method'

    def lookups(self, request, model_admin):
        def custom_sql():
            query = """WITH RECURSIVE t AS (
                    (SELECT method FROM applogs_serverrecord ORDER BY method LIMIT 1) UNION ALL
                    SELECT (SELECT method FROM applogs_serverrecord WHERE method > t.method ORDER BY method LIMIT 1)
                    FROM t WHERE t.method IS NOT NULL ) SELECT method FROM t WHERE method IS NOT NULL;"""
            with connections['applogs'].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return rows
        return [(row[0], row[0]) for row in custom_sql()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(Q(method=self.value()))


class LevelFilter(admin.SimpleListFilter):
    title = 'Уровень'
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        def custom_sql():
            query = """WITH RECURSIVE t AS (
                    (SELECT level FROM applogs_serverrecord ORDER BY level LIMIT 1) UNION ALL
                    SELECT (SELECT level FROM applogs_serverrecord WHERE level > t.level ORDER BY level LIMIT 1)
                    FROM t WHERE t.level IS NOT NULL ) SELECT level FROM t WHERE level IS NOT NULL;"""
            with connections['applogs'].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return rows
        return [(row[0], row[0]) for row in custom_sql()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(Q(level=self.value()))


class HeadquarterFilter(admin.SimpleListFilter):
    title = 'Клиент'
    parameter_name = 'headquater'

    def lookups(self, request, model_admin):
        def custom_sql():
            query = """WITH RECURSIVE t AS (
                    (SELECT headquater FROM applogs_serverrecord ORDER BY headquater LIMIT 1) UNION ALL
                    SELECT (SELECT headquater FROM applogs_serverrecord WHERE headquater > t.headquater ORDER BY headquater LIMIT 1)
                    FROM t WHERE t.headquater IS NOT NULL ) SELECT headquater FROM t WHERE headquater IS NOT NULL;"""
            with connections['applogs'].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return rows
        return [(row[0], row[0]) for row in custom_sql()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(Q(headquater=self.value()))


@admin.register(ServerRecord)
class ServerRecordAdmin(AdminExportMixin, admin.ModelAdmin):
    list_display = ('created_at', 'headquater', 'source', 'method', 'level', 'duration_rounded', 'html_message')
    list_filter = (SourceFilter, MethodFilter, LevelFilter, HeadquarterFilter)
    search_fields = ('message', 'tags')
    form = ServerRecordForm

    def html_message(self, obj):
        return format_html('<pre>{}</pre>', obj.message[:200])
    html_message.short_description = 'Описание'

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
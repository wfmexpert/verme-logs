from datetime import timedelta

import xlwt
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import connections
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import make_naive

from xlsexport.mixins import AdminExportMixin
from .forms import ServerRecordForm
from .models import ClientRecord, ServerRecord
from .utils import XLSWriterUtil


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
            for c, col_name in enumerate(
                    ['ДАТА СОЗДАНИЯ', 'КЛИЕНТ', 'ИСТОЧНИК', 'МЕТОД', 'ВАЖНОСТЬ', 'ПРОДОЛЖИТЕЛЬНОСТЬ', 'ОПИСАНИЕ']):
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


class IndexFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''

    def lookups(self, request, model_admin):
        def custom_sql():
            query = f"""WITH RECURSIVE t AS (
                    (SELECT {self.parameter_name} FROM applogs_serverrecord ORDER BY {self.parameter_name} LIMIT 1) UNION ALL
                    SELECT (SELECT {self.parameter_name} FROM applogs_serverrecord WHERE {self.parameter_name} > t.{self.parameter_name} ORDER BY {self.parameter_name} LIMIT 1)
                    FROM t WHERE t.{self.parameter_name} IS NOT NULL ) SELECT {self.parameter_name} FROM t WHERE {self.parameter_name} IS NOT NULL;"""
            with connections['applogs'].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return rows

        return [(row[0], row[0]) for row in custom_sql()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        query_dict = dict()
        query_dict.update({f'{self.parameter_name}': self.value()})
        return queryset.filter(Q(**query_dict))


class SourceFilter(IndexFilter):
    title = 'Источник'
    parameter_name = 'source'


class MethodFilter(IndexFilter):
    title = 'Метод'
    parameter_name = 'method'


class LevelFilter(IndexFilter):
    title = 'Уровень'
    parameter_name = 'level'


class HeadquarterFilter(IndexFilter):
    title = 'Клиент'
    parameter_name = 'headquater'


class CountEstimatePaginator(Paginator):
    """
    Предполагается использование PostgreSQL

    Для маленьких таблиц (<5000 строк) выводится точное количество записей, в остальных случаях - оценочное
    """

    def _get_count(self):
        if isinstance(self.object_list, QuerySet) and hasattr(self.object_list, 'count_estimate'):
            return self.object_list.count_estimate()

        return self.object_list.count()

    count = property(_get_count)


@admin.register(ServerRecord)
class ServerRecordAdmin(AdminExportMixin, admin.ModelAdmin):
    list_display = ('created_at_str', 'headquater', 'source', 'method', 'level', 'duration_rounded', 'html_message')
    readonly_fields = ('created_at_str',)
    list_filter = (SourceFilter, MethodFilter, LevelFilter, HeadquarterFilter)
    search_fields = ('message', 'tags')
    form = ServerRecordForm
    show_full_result_count = False
    paginator = CountEstimatePaginator

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

    def created_at_str(self, obj):
        """Отображение времени события с секундами"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

    created_at_str.short_description = 'дата создания'

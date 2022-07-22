from django.core.exceptions import FieldDoesNotExist

from django.db import models
from django.apps import apps
from django.http import HttpResponse
from django.utils.timezone import get_current_timezone
from datetime import datetime, date, timedelta

import xlsxwriter
import xlwt
import csv
import io
import json
import string

from .parsers import XLSParser

try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

# Форматы экспорта
EXPORT_FORMAT_CHOICES = (
    ("xlsx", "XLSX"),
    ("xls", "XLS"),
    ("csv", "CSV"),
)


class ExportTemplate(models.Model):
    name = models.CharField(verbose_name="название", max_length=255, blank=False, null=False)
    code = models.CharField(verbose_name="код", max_length=255, blank=False, null=False, unique=True)
    format = models.CharField(
        verbose_name="формат",
        max_length=5,
        choices=EXPORT_FORMAT_CHOICES,
        default=EXPORT_FORMAT_CHOICES[0][0],
        blank=False,
        null=False,
    )
    model = models.CharField(verbose_name="модель", max_length=64, blank=True, null=True)
    queryset = JSONField(verbose_name="queryset", default=None, null=True, blank=True)
    params = JSONField(verbose_name="параметры", default=None, null=True, blank=True)
    default = models.BooleanField(verbose_name="по умолчанию", default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Шаблоны импорта / экспорта в Excel"
        verbose_name_plural = "Шаблоны импорта / экспорта в Excel"

    def to_export(self, queryset=None):
        if self.format == "xlsx":
            return self.to_xlsx(queryset)
        elif self.format == "xls":
            return self.to_xls(queryset)
        elif self.format == "csv":
            return self.to_csv(queryset)
        return None

    def get_model(self):
        model = apps.get_model(*(self.model.split(".", 1)))
        return model

    def get_model_fields(self):
        fields = self.get_model()._meta.get_fields()
        return fields

    def get_param_fields(self):
        fields = self.get_model_fields()
        param_fields = self.params.get("fields", list())
        if not param_fields:
            for field in fields:
                if isinstance(field, models.ManyToOneRel):
                    continue
                param_fields.append(
                    {
                        "name": field.verbose_name if hasattr(field, "verbose_name") else field.name,
                        "field": field.name,
                        "key_field": field.primary_key,
                        "export_ignore": False,
                        "import_ignore": False,
                    }
                )
        return param_fields, fields

    def get_key_fields(self):
        param_fields, fields = self.get_param_fields()
        if not param_fields:
            return None
        key_fields = list()
        for field in param_fields:
            if field.get("key_field"):
                key_fields.append(field)
        return key_fields

    def get_queryset(self, queryset=None):
        # @author p.ilinskiy@verme.ru
        # Критическая уязвимость, в случае получения пустого запроса получаем все данные
        if queryset is None:
            queryset = self.get_model().objects.all()
            if self.queryset:
                queryset = queryset.filter(**self.queryset)
        return queryset

    def modify_queryset(self, queryset=None, param_fields=None):
        if not param_fields:
            return queryset
        fields_qs = list()

        for idx, field in enumerate(param_fields):
            if field.get("export_ignore", False):
                continue
            field_name = field.get("field").split(".")
            if len(field_name) > 1:
                field_name.pop()
            for f in self.get_model_fields():
                if field_name[0] == f.name and f.is_relation and f.related_model is not None and not f.many_to_many:
                    if len(field_name) > 1:
                        try:
                            related_field = f.related_model._meta.get_field(field_name[1])
                        except BaseException:
                            related_field = None
                        if isinstance(related_field, JSONField):
                            field_name.pop()
                    fields_qs.append("__".join(field_name))
        if fields_qs:
            queryset = queryset.select_related(*fields_qs)
        return queryset

    def check_fields(self):
        # TODO
        pass

    def get_export_fields(self):
        # TODO
        pass

    def get_attr_value(self, obj, field):
        # Делим поле на части по разделителю точке
        field = field.get("field").split(".")
        for ind, field_name in enumerate(field):
            # Берем значение аттрибута по имени. Может быть поле, может быть значение свойства
            value = getattr(obj, field_name, None)
            # Пробуем найти поле модели
            try:
                item_field = obj._meta.get_field(field_name)
            except BaseException:
                item_field = None
            if item_field and (isinstance(item_field, models.ForeignKey) or isinstance(item_field, models.OneToOneField) or isinstance(item_field, models.OneToOneRel)):
                # Если поле - ссылка на объект, его используем как объект для получения следующих значений
                obj = value
            elif item_field and item_field.many_to_many:
                # Если есть поле и оно ManyToMany - берем в качестве названия колонки следующую часть field
                if ind < len(field) - 1:
                    column_name = field[ind + 1]
                    value = "|".join(value.values_list(column_name, flat=True))
                else:
                    value = None
                break  # Для ManyToMany допустима только одна вложенность
            elif isinstance(item_field, JSONField):
                # Если поле Json, берем значение по ключу, если есть следующая часть поля
                if ind < len(field) - 1:
                    column_name = field[ind + 1]
                    value = (getattr(obj, field_name, {}) or {}).get(column_name)
                else:
                    value = json.dumps(getattr(obj, field_name), ensure_ascii=False)
                break  # Для JSONField допустима только одна вложенность

        if value is None:  # Output False explicitly
            value = ""
        return value

    def to_xlsx(self, queryset=None):
        param_fields, fields = self.get_param_fields()
        queryset = self.get_queryset(queryset)

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(output, {"constant_memory": True})
        worksheet = workbook.add_worksheet(self.code)

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({"bold": True})

        letters = string.ascii_uppercase

        # Установка ширины колонок и заполнение заголовков
        for idx, field in enumerate(param_fields):
            export_ignore_field = field.get("export_ignore", False)
            if export_ignore_field:
                continue
            worksheet.set_column(f"{letters[idx]}:{letters[idx]}", field.get("width", 15))
            worksheet.write(f"{letters[idx]}1", f'{field.get("name")}', bold)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 1

        # Modify queryset with select_related statements
        queryset = self.modify_queryset(queryset, param_fields)

        # Iterate over the data and write it out row by row.
        for item in queryset.iterator():
            for idx, field in enumerate(param_fields):
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                cell_format = None

                attr_value = self.get_attr_value(item, field)
                attr_format = field.get("format", "").strip()
                if isinstance(attr_value, datetime):
                    attr_value = attr_value.astimezone(get_current_timezone())
                    if attr_format:
                        attr_value = attr_value.strftime(attr_format)
                    else:
                        cell_format = workbook.add_format()
                        cell_format.set_num_format(attr_format)
                if isinstance(attr_value, date):
                    if attr_format:
                        if attr_format.startswith("%"):
                            attr_value = attr_value.strftime(attr_format)
                        else:
                            cell_format = workbook.add_format()
                            cell_format.set_num_format(attr_format)
                if isinstance(attr_value, timedelta):
                    attr_value = int(attr_value.total_seconds() / 60)
                if isinstance(attr_value, float) or isinstance(attr_value, int):
                    if attr_format:
                        cell_format = workbook.add_format()
                        cell_format.set_num_format(attr_format)
                if not cell_format:
                    worksheet.write(row, idx, str(attr_value))
                else:
                    worksheet.write(row, idx, attr_value, cell_format)
            row += 1

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Construct a server response.
        response = HttpResponse(
            output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = self.params.get("filename", self.code)
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
        return response

    def to_xls(self, queryset=None):
        param_fields, fields = self.get_param_fields()
        queryset = self.get_queryset(queryset)

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlwt.Workbook(encoding="utf-8", style_compression=2)
        worksheet = workbook.add_sheet(self.code, cell_overwrite_ok=False)

        bold = xlwt.easyxf("font: bold on")

        # Установка ширины колонок и заполнение заголовков
        for idx, field in enumerate(param_fields):
            export_ignore_field = field.get("export_ignore", False)
            if export_ignore_field:
                continue
            worksheet.write(0, idx, field.get("name"), bold)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 1

        # Modify queryset with select_related statements
        queryset = self.modify_queryset(queryset, param_fields)
        queryset = queryset[:65000]

        # Iterate over the data and write it out row by row.
        for item in queryset.iterator():
            for idx, field in enumerate(param_fields):
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                cell_format = None

                attr_value = self.get_attr_value(item, field)
                attr_format = field.get("format", "").strip()
                if isinstance(attr_value, datetime):
                    attr_value = attr_value.astimezone(get_current_timezone())
                    if attr_format:
                        attr_value = attr_value.strftime(attr_format)
                    else:
                        cell_format = workbook.add_format()
                        cell_format.set_num_format(attr_format)
                if isinstance(attr_value, date):
                    if attr_format:
                        if attr_format.startswith("%"):
                            attr_value = attr_value.strftime(attr_format)
                        else:
                            cell_format = xlwt.XFStyle()
                            cell_format.num_format_str = attr_format
                if isinstance(attr_value, timedelta):
                    attr_value = int(attr_value.total_seconds() / 60)
                if isinstance(attr_value, float):
                    if attr_format:
                        cell_format = xlwt.XFStyle()
                        cell_format.num_format_str = attr_format
                if not cell_format:
                    worksheet.write(row, idx, str(attr_value))
                else:
                    worksheet.write(row, idx, attr_value, cell_format)
            row += 1

        workbook.save(output)

        # Rewind the buffer.
        output.seek(0)

        # Construct a server response.
        response = HttpResponse(output.read(), content_type="application/vnd.ms-excel")
        filename = self.params.get("filename", self.code)
        response["Content-Disposition"] = f'attachment; filename="{filename}.xls"'
        return response

    def to_csv(self, queryset=None):
        param_fields, fields = self.get_param_fields()
        queryset = self.get_queryset(queryset)

        filename = self.params.get("filename", self.code)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

        # Create a csv writer.
        writer = csv.writer(response)

        # Заполнение заголовков
        header = []
        for field in param_fields:
            export_ignore_field = field.get("export_ignore", False)
            if export_ignore_field:
                continue
            header.append(field.get("name"))

        writer.writerow(header)

        # Modify queryset with select_related statements
        queryset = self.modify_queryset(queryset, param_fields)

        # Iterate over the data and write it out row by row.
        data = []
        for item in queryset.iterator():
            for field in param_fields:
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue

                attr_value = self.get_attr_value(item, field)
                attr_format = field.get("format", "").strip()
                if isinstance(attr_value, datetime):
                    attr_value = attr_value.astimezone(get_current_timezone())
                    if attr_format:
                        if attr_format.startswith("%"):
                            attr_value = attr_value.strftime(attr_format)
                        else:
                            attr_value = str(attr_value)
                if isinstance(attr_value, date):
                    if attr_format:
                        if attr_format.startswith("%"):
                            attr_value = attr_value.strftime(attr_format)
                        else:
                            attr_value = str(attr_value)
                if isinstance(attr_value, timedelta):
                    attr_value = int(attr_value.total_seconds() / 60)
                data.append(attr_value)
            writer.writerow(data)
            data = []

        return response

    def from_xlsx(self, file=None):
        parser = XLSParser()
        errors = parser.parse(self, file.read())
        return errors

    def to_import(self, file=None):
        if self.format == "xlsx" or self.format == "xls":
            return self.from_xlsx(file)
        elif self.format == "csv":
            return None
        return None


class ImportTemplate(ExportTemplate):
    class Meta:
        proxy = True
        verbose_name = "Импорт из Excel"
        verbose_name_plural = "Импорт из Excel"

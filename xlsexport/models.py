from django.contrib.postgres.fields import JSONField
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.utils.safestring import mark_safe

from django.db import models
from django.apps import apps
from django.http import HttpResponse
from datetime import datetime, date

import xlsxwriter, xlwt
import io
import string

from .parsers import XLSParser

# Форматы экспорта
EXPORT_FORMAT_CHOICES = (
    ("xlsx", "XLSX"),
    ("xls", "XLS"),
    ("csv", "CSV"),
)


class ExportTemplate(models.Model):
    name = models.CharField(verbose_name='название', max_length=255, blank=False, null=False)
    code = models.CharField(verbose_name='код', max_length=255, blank=False, null=False, unique=True)
    format = models.CharField(verbose_name='формат', max_length=5, choices=EXPORT_FORMAT_CHOICES,
                              default=EXPORT_FORMAT_CHOICES[0][0], blank=False, null=False)
    model = models.CharField(verbose_name='модель', max_length=64, blank=True, null=True)
    queryset = JSONField(verbose_name='queryset', default=None, null=True, blank=True)
    params = JSONField(verbose_name='параметры', default=None, null=True, blank=True)
    default = models.BooleanField(verbose_name='по умолчанию', default=False)

    class Meta:
        verbose_name = 'Шаблон отчета'
        verbose_name_plural = 'Шаблоны отчетов'

    def to_export(self, queryset=None):
        if self.format == 'xlsx':
            return self.to_xlsx(queryset)
        elif self.format == 'xls':
            return self.to_xls(queryset)
        elif self.format == 'csv':
            return self.to_xlsx(queryset)
        return None

    def get_model(self):
        model = apps.get_model(*(self.model.split('.', 1)))
        return model

    def get_model_fields(self):
        fields = self.get_model()._meta.get_fields()
        return fields

    def get_param_fields(self):
        param_fields = self.params.get('fields')
        fields = param_fields or self.get_model_fields()
        return param_fields, fields

    def get_key_fields(self):
        param_fields, fields = self.get_param_fields()
        if not param_fields:
            return None
        key_fields = list()
        for field in param_fields:
            if field.get('key_field'):
                key_fields.append(field)
        return key_fields

    def get_queryset(self, queryset=None):
        if not queryset:
            queryset = self.get_model().objects.all()
        if self.queryset:
            queryset = queryset.filter(**self.queryset)
        return queryset

    def check_fields(self):
        # TODO
        pass

    def get_export_fields(self):
        # TODO
        pass

    def to_xlsx(self, queryset=None):
        param_fields, fields = self.get_param_fields()
        queryset = self.get_queryset(queryset)

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(self.code)

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})

        letters = string.ascii_uppercase

        # Установка ширины колонок и заполнение заголовков
        for idx, field in enumerate(fields):
            if not param_fields:
                worksheet.set_column(f'{letters[idx]}:{letters[idx]}', 15)
                worksheet.write(f'{letters[idx]}1', f'{field.verbose_name}', bold)
            else:
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                worksheet.set_column(f'{letters[idx]}:{letters[idx]}', field.get("width", 15))
                worksheet.write(f'{letters[idx]}1', f'{field.get("name")}', bold)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 1

        # Iterate over the data and write it out row by row.
        for item in queryset:
            for idx, field in enumerate(fields):
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                cell_format = None
                if not param_fields:
                    attr_value = getattr(item, field.name)
                else:
                    try:
                        field_name = field.get('field').split('.')
                        attr_value = getattr(item, field_name[0])
                        for x in range(1, len(field_name)):
                            attr_value = getattr(attr_value, field_name[x])
                    except AttributeError:
                        msg = f"Поле {field.get('field')} отсутствует в объекте"
                        return HttpResponse(msg)

                if isinstance(attr_value, datetime):
                    attr_value = attr_value.astimezone()
                    if param_fields and field.get('format'):
                        attr_value = attr_value.strftime(field.get('format'))
                if isinstance(attr_value, float):
                    if param_fields and field.get('format'):
                        cell_format = workbook.add_format()
                        cell_format.set_num_format(field.get('format'))
                if not cell_format:
                    worksheet.write(row, idx, str(attr_value))
                else:
                    worksheet.write(row, idx, attr_value, cell_format)
            row += 1

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Construct a server response.
        response = HttpResponse(output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = self.params.get('filename', self.code)
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response

    def to_xls(self, queryset=None):
        param_fields, fields = self.get_param_fields()
        queryset = self.get_queryset(queryset)[:65000]

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlwt.Workbook(encoding='utf-8', style_compression=2)
        worksheet = workbook.add_sheet(self.code, cell_overwrite_ok=False)

        bold = xlwt.easyxf('font: bold on')

        # Установка ширины колонок и заполнение заголовков
        for idx, field in enumerate(fields):
            if not param_fields:
                worksheet.write(0, idx, field.verbose_name, bold)
            else:
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                worksheet.write(0, idx, field.get("name"), bold)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 1

        # Iterate over the data and write it out row by row.
        for item in queryset:
            for idx, field in enumerate(fields):
                export_ignore_field = field.get("export_ignore", False)
                if export_ignore_field:
                    continue
                cell_format = None
                if not param_fields:
                    attr_value = getattr(item, field.name)
                else:
                    try:
                        field_name = field.get('field').split('.')
                        attr_value = getattr(item, field_name[0])
                        for x in range(1, len(field_name)):
                            attr_value = getattr(attr_value, field_name[x])
                    except AttributeError:
                        msg = f"Поле {field.get('field')} отсутствует в объекте"
                        return HttpResponse(msg)
                if isinstance(attr_value, datetime):
                    attr_value = attr_value.astimezone()
                    if param_fields and field.get('format'):
                        attr_value = attr_value.strftime(field.get('format'))
                if isinstance(attr_value, float):
                    if param_fields and field.get('format'):
                        cell_format = xlwt.XFStyle()
                        cell_format.num_format_str = field.get('format')
                if not cell_format:
                    worksheet.write(row, idx, str(attr_value))
                else:
                    worksheet.write(row, idx, attr_value, cell_format)
            row += 1

        workbook.save(output)

        # Rewind the buffer.
        output.seek(0)

        # Construct a server response.
        response = HttpResponse(output.read(),
                                content_type='application/vnd.ms-excel')
        filename = self.params.get('filename', self.code)
        response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
        return response


    def from_xlsx(self, file=None):
        parser = XLSParser()
        errors = parser.parse(self, file.read())
        return errors

    def to_import(self, file=None):
        if self.format == 'xlsx' or self.format == 'xls':
            return self.from_xlsx(file)
        elif self.format == 'csv':
            return None
        return None


class ImportTemplate(ExportTemplate):

    class Meta:
        proxy = True
        verbose_name = 'Импорт из XLSX/XLS'
        verbose_name_plural = 'Импорт из XLSX/XLS'

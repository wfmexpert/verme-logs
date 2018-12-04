from django.contrib.postgres.fields import JSONField
from django.db import models
from django.apps import apps
from django.http import HttpResponse

import xlsxwriter
import io
import string

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

    class Meta:
        verbose_name = 'Шаблон отчета'
        verbose_name_plural = 'Шаблоны отчетов'

    def to_export(self):
        if self.format == 'xlsx':
            return self.to_xlsx()
        elif self.format == 'xls':
            return self.to_xlsx()
        elif self.format == 'csv':
            return self.to_xlsx()
        return None

    def get_fields_queryset(self):
        model = apps.get_model(*(self.model.split('.', 1)))
        fields = model._meta.get_fields()
        queryset = model.objects.all()
        return fields, queryset

    def to_xlsx(self):
        fields, queryset = self.get_fields_queryset()

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})

        letters = string.ascii_uppercase

        # Установка ширины колонок и заполнение заголовков
        for idx, field in enumerate(fields):
            print(idx, field)
            worksheet.set_column(f'{letters[idx]}:{letters[idx]}', 15)
            worksheet.write(f'{letters[idx]}{idx}', f'{field.name}', bold)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 1

        # Iterate over the data and write it out row by row.
        for item in queryset:
            for idx, field in enumerate(fields):
                worksheet.write(row, idx, getattr(item, field))
            row += 1

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Construct a server response.
        response = HttpResponse(output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response

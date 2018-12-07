import datetime
import xlrd

from django.db import transaction
from django.db.models import Q

from collections import defaultdict

from .methods import *


class XLSParser:
    """
    Парсер xls-файлов
    """

    def __init__(self):
        self.item_data = {}
        self.processed_items = set()
        self.created_items = defaultdict(list)

    def parse(self, template, file_contents):
        rb = xlrd.open_workbook(file_contents=file_contents)
        sheet = rb.sheet_by_index(0)
        errors = []
        for rownum in range(1, sheet.nrows):
            row = sheet.row_values(rownum)
            try:
                self.item_date = self.get_struct_from_row(row, rb, template)
                self.process_item_data(template)
            except Exception as exc:
                errors.append({'rownum': rownum, 'exc': exc})
        return errors

    def process_item_data(self, template):
        model = template.get_model()
        param_fields, fields = template.get_param_fields()
        key_fields = template.get_key_fields()
        if not param_fields or not key_fields:
            return None

        print('KEY FIELDS', key_fields)
        # Список ключевых полей
        key_fields_list = set()
        for key_field in key_fields:
            key_fields_list.add(key_field['field'])

        # Для update_or_create
        result_query = dict()

        query = dict()
        defaults = dict()

        for row_data in self.item_data:
            if param_fields[row_data].get('import_ignore', True):
                continue
            if row_data in key_fields_list:
                # Если есть указания ключевых полей через точку, то они должны быть преобразованы
                # в __ для формирования queryset
                query.update({row_data.replace('.', '__'): self.item_data[row_data]})
            else:
                # Если поля не ключевые, то нужно сначала найти объекты
                splitted_fields = row_data.split('.')
                if len(splitted_fields) > 1:
                    # Определяем тип поля
                    field = model.get_field(splitted_fields[0])
                    curr_idx = 1
                    while True:
                        if curr_idx > len(splitted_fields):
                            break
                        # Если поле - связь к другой модели
                        if field.is_relation and field.related_model:
                            # Обновляем модель
                            model = field.related_model
                            # Обновляем поле
                            field = model.get_field(splitted_fields[curr_idx])
                        else:
                            # Формируем массив для поиска объекта модели
                            attr_query_dict = {splitted_fields[curr_idx]: self.item_data[row_data]}
                            attr_value = model.objects.filter(**attr_query_dict).first()
                            # Убираем последнее поле, т.к. оно для поиска объекта модели
                            # и устанавливаем объект модели
                            splitted_fields.pop()
                            # TODO пока только 1 уровень, например organization.code
                            # TODO organization.headquater.code не сработает
                            #model_curr_idx = 1
                            #while True:
                            #    if model_curr_idx > len(splitted_fields):
                            #        break

                            # organization.headquater
                            defaults.update({'__'.join(splitted_fields): attr_value})

                        # Обновляем индекс
                        curr_idx += 1
                else:
                    defaults.update({row_data: self.item_data[row_data]})

        result_query.update(query, defaults=defaults)
        print ("RESULT_QUERY", result_query)

        with transaction.atomic():
            try:
                model_obj, created = model.update_or_create(result_query)
                if created:
                    self.created_items[model_obj] = self.item_data
            except Exception:
                raise
        self.processed_items.add(model_obj)

    @staticmethod
    def get_struct_from_row(row, rb, template):

        def get_formatted_field(value):
            try:
                value = float(value)
                return str(value)
            except (TypeError, ValueError):
                return get_cell_date(value)

        def get_cell_date(cell):
            return str(cell).strip() and datetime.datetime(*xlrd.xldate_as_tuple(cell, rb.datemode)) or None

        def get_number(value):
            try:
                number = int(value)
                return str(number)
            except (TypeError, ValueError):
                return value

        def get_int_as_string(value):
            if isinstance(value, str):
                return value
            return str(int(value))

        def clean_value(value):
            if isinstance(value, (bytes, str)):
                if value:
                    if isinstance(value, bytes):
                        value = value.encode('utf-8')
                    value = value.strip().replace("'", '')
                else:
                    value = ''
            return value

        result = dict()
        param_fields, fields = template.get_param_fields
        for idx, item in enumerate(row):
            if 'format' in param_fields[idx]:
                attr_value = get_formatted_field(clean_value(row[idx]))
            else:
                attr_value = get_int_as_string(clean_value(row[idx]))
            result.update({param_fields[idx]: attr_value})
        return result
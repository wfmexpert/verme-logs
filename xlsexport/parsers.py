import datetime
import xlrd
import re

from django.db import transaction
from django.db.models import Q

from collections import defaultdict


class CustomException(Exception):
    pass


class XLSParser:
    """
    Парсер xls-файлов
    """

    def __init__(self):
        self.cache_dict = dict()
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
                self.item_data = self.get_struct_from_row(row, rb, template)
                self.process_item_data(template)
            except Exception as exc:
                errors.append({'rownum': rownum, 'exc': exc})
        return errors

    def get_attr_value(self, model, row_data, splitted_fields):
        # Определяем тип поля
        field = model._meta.get_field(splitted_fields[0])
        # Если поле - связь к другой модели
        if field.is_relation and field.related_model:
            # Обновляем модель
            model = field.related_model
            # Формируем массив для поиска объекта модели
            attr_query_dict = {splitted_fields[1]: self.item_data[row_data]}
        else:
            # Формируем массив для поиска объекта модели
            attr_query_dict = {splitted_fields[0]: self.item_data[row_data]}
        attr_value = model.objects.filter(**attr_query_dict).first()
        return attr_value

    def get_attr_value_ext(self, model, row_data):
        # Делим поле по разделителю
        splitted_fields = row_data.split('.')
        splitted_length = len(splitted_fields)

        current_idx = 0
        processed_model_list = list()
        processed_model_list.append(model)
        attr_value = None
        many_to_many_values = list()
        m2m_flag = False

        while True:
            if not current_idx < splitted_length:
                break
            # Выбираем поле и модель
            current_field = splitted_fields[current_idx]
            field = model._meta.get_field(current_field)
            # Если поле - связь к другой модели
            if field.is_relation and field.related_model:
                if field.many_to_many:
                    m2m_flag = True
                # Обновляем модель
                model = field.related_model
                processed_model_list.append(model)
            else:
                data_values = str(self.item_data[row_data]).split('|')
                if current_idx > 0:
                    if len(data_values) > 1:
                        for s_value in data_values:
                            # Формируем массив для поиска объекта модели
                            attr_query_dict = {splitted_fields[current_idx]: s_value}
                            # Получили объект модели по значению поля
                            attr_value = model.objects.filter(**attr_query_dict).first()
                            many_to_many_values.append(attr_value)
                        attr_value = many_to_many_values
                    else:
                        # Формируем массив для поиска объекта модели
                        attr_query_dict = {splitted_fields[current_idx]: self.item_data[row_data]}
                        # Получили объект модели по значению поля
                        attr_value = model.objects.filter(**attr_query_dict).first()
                        if m2m_flag:
                            many_to_many_values.append(attr_value)
                            attr_value = many_to_many_values
                else:
                    attr_value = self.item_data[row_data]
            current_idx += 1

        current_idx2 = splitted_length - 2
        # Убираем последнюю модель из списка обработанных
        # т.к. по ней уже имеем объект
        processed_model_list.pop()
        current_value = attr_value

        while True:
            if current_idx2 < 1:
                break
            current_model = processed_model_list.pop()
            #
            current_field = splitted_fields[current_idx2]
            field = current_model._meta.get_field(current_field)
            #
            if not field.many_to_many:
                current_object_attr_query = {splitted_fields[current_idx2]: current_value}

                if processed_model_list:
                    current_value = current_model.objects.filter(**current_object_attr_query).first()
                else:
                    current_value = current_object_attr_query
            # ManytoMany Field
            else:
                search_values = current_value.split('|')
                for s_value in search_values:
                    current_object_attr_query = {splitted_fields[current_idx2]: s_value}
                    if processed_model_list:
                        current_value = current_model.objects.filter(**current_object_attr_query).first()
                    else:
                        current_value = current_object_attr_query
                    many_to_many_values.append(current_value)

            current_idx2 -= 1

        result_dict = dict()
        m2m_dict = dict()
        if splitted_length > 1:
            if many_to_many_values:
                m2m_dict = {splitted_fields[0]: many_to_many_values}
            else:
                result_dict = {splitted_fields[0]: current_value}
        else:
            if many_to_many_values:
                m2m_dict = {splitted_fields[0]: many_to_many_values}
            else:
                result_dict = {splitted_fields[0]: attr_value}
        return result_dict, m2m_dict

    def process_item_data(self, template):
        model = template.get_model()
        param_fields, fields = template.get_param_fields()
        key_fields = template.get_key_fields()

        if not param_fields or not key_fields:
            raise CustomException(f"Не указаны поля или ключевые поля в шаблоне")

        # Список ключевых полей
        key_fields_list = set()
        for key_field in key_fields:
            key_fields_list.add(key_field['field'])

        # Список игнорируемых полей
        ignore_fields_list = set()
        for param_field in param_fields:
            if param_field.get('import_ignore', True):
                ignore_fields_list.add(param_field['field'])

        # Для update_or_create
        result_query = dict()

        query = dict()
        defaults = dict()
        m2m = dict()
        cache_set = list()

        for row_data in self.item_data:
            if row_data in ignore_fields_list:
                continue
            # Если поле ключевое
            if row_data in key_fields_list:
                cache_set.append(self.item_data[row_data])
                query_dict, m2m_dict = self.get_attr_value_ext(model, row_data)
                query.update(query_dict)
                m2m.update(m2m_dict)
            else:
                # Если поле не ключевое
                query_dict, m2m_dict = self.get_attr_value_ext(model, row_data)
                defaults.update(query_dict)
                m2m.update(m2m_dict)

        target_object = None
        if cache_set:
            cache_tuple = tuple(i for i in cache_set)
            if cache_tuple in self.cache_dict:
                target_object = self.cache_dict.get(cache_tuple)
            else:
                target_object = model.objects.filter(**query).first()
                self.cache_dict.update({cache_tuple: target_object})

        with transaction.atomic():
            def compile_expression(expression):
                return compile(expression, f'm2m_set', 'exec')

            def exec_expression(expression, target_object, m2m=None):
                locals_ = {
                    'target_object': target_object,
                    'm2m': m2m
                }
                exec(compile_expression(expression), None, locals_)
                return locals_.get('result', None)
            try:
                if target_object:
                    for key, value in defaults.items():
                        setattr(target_object, key, value)
                    target_object.save()

                    # Установка M2M полей
                    for m2m_key, m2m_value in m2m.items():
                        expression = f'target_object.{m2m_key}.set(m2m)'
                        exec_expression(expression, target_object, m2m_value)
                else:
                    result_query.update(query)
                    result_query.update(defaults)
                    target_object = model.objects.create(**result_query)

                    # Установка M2M полей
                    for m2m_key, m2m_value in m2m.items():
                        expression = f'target_object.{m2m_key}.set(m2m)'
                        exec_expression(expression, target_object, m2m_value)
                    self.created_items[target_object] = self.item_data
            except Exception:
                raise
        self.processed_items.add(target_object)

    @staticmethod
    def get_struct_from_row(row, rb, template):

        def get_formatted_field(value, format):
            pattern = re.compile("^0[.]0+$")
            if pattern.match(format):
                value = float(value)
                return str(value)
            return get_cell_date(value)

        def get_cell_date(cell):
            try:
                return str(cell).strip() and datetime.datetime(*xlrd.xldate_as_tuple(cell, rb.datemode)) or None
            except TypeError:
                return cell

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
        param_fields, fields = template.get_param_fields()
        for idx, item in enumerate(row):
            param_field = param_fields[idx]
            field_path = param_field['field']
            if 'format' in param_field:
                attr_value = get_formatted_field(clean_value(row[idx]), param_field['format'])
            elif field_path.count('.') == 0 and template.get_model()._meta.get_field(field_path).get_internal_type() == 'DurationField':
                # если это простое поле типа min_value (а не table.code), и в модели там хранится продолжительность, делаем продолжительность
                attr_value = datetime.timedelta(minutes=int(row[idx]) if row[idx] else 0)
            else:
                attr_value = get_int_as_string(clean_value(row[idx]))
            result.update({field_path: attr_value})
        return result

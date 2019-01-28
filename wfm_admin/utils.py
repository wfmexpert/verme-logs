from django.contrib import admin
from django.contrib.admin.utils import display_for_field, lookup_field


def renamed(attr_name, new_label):
    """
    Возвращает переименованное поле для админского list_display.
    Пример:
    class SmthAdmin(admin.ModelAdmin):
        value_upd = renamed('value', 'значеие')
        list_display = ('name', 'value_upd')
    """
    def func(self, obj):
        f, _, value = lookup_field(attr_name, obj, self)
        return display_for_field(value, f, self.get_empty_value_display())
    func.short_description = new_label
    func.admin_order_field = attr_name
    return func


class DateFieldRangeFilter(admin.FieldListFilter):
    """
    Создаёт фильтр по интервалу дат.
    В отличии от DateFieldListFilter позволяет указать проивольные начальную и конечную даты.
    """
    template = 'admin/date_range_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_path = field_path
        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lte' % field_path
        self.lookup_value_since = params.get(self.lookup_kwarg_since, '')
        self.lookup_value_until = params.get(self.lookup_kwarg_until, '')
        self.links = ()
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_until]

    def choices(self, changelist):
        return []

from django.contrib.admin import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Value
from django.db.models.functions import Concat
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserChangeForm
from social_django.models import UserSocialAuth

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class UserSocialAuthInline(TabularInline):
    model = UserSocialAuth
    extra = 0
    max_num = 1


class UserChangeFormAdmin(UserChangeForm):
    password = ReadOnlyPasswordHashField(label="Пароль",
                                         help_text="<a href=\"../password/\">Сменить пароль</a>.")


site.unregister(User)
@register(User)
class UserAccessAdmin(UserAdmin):
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    full_name.short_description = 'ФИО'
    full_name.admin_order_field = 'full_name'

    form = UserChangeFormAdmin
    list_display = ('username', 'email', full_name, 'is_active', 'is_superuser', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'last_name', 'first_name',
                           'email')}),
        ('Доступ', {'fields': ('is_active', 'is_staff', 'is_superuser',
                               'groups', 'user_permissions')}),
    )
    list_filter = ()
    inlines = [UserSocialAuthInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(full_name=Concat('first_name', Value(' '), 'last_name'))


class WfmAdminSite(AdminSite):
    sections = None

    def __init__(self, *args, **kwargs):
        super(WfmAdminSite, self).__init__(*args, **kwargs)
        self.sections = settings.ADMIN_SECTIONS
        self.columns = settings.ADMIN_COLUMNS
        self.site_header = 'Настройки'
        self.index_title = self.site_header
        self._registry.update(site._registry)

    def get_app_list(self, request):
        """
        Вот тут то мы и подменим логику "Приложение->модели" на "Секция->модели"
        :param request:
        :return:
        """
        sections_list = []
        app_list = super(self.__class__, self).get_app_list(request)
        self.current_user = request.user

        if len(app_list) == 0:  # в тестах список пустой, пропускаем. TODO
            return app_list

        def get_model_from_app_list(app_name, obj_name):
            try:
                app = [app for app in app_list if app['app_label'] == app_name][0]
            except IndexError:
                return
            try:
                return [model for model in app['models'] if model['object_name'] == obj_name][0]
            except IndexError:
                return

        def check_section_access(self, key):
            for model in self.sections[key]:
                splitted_value = model['model'].lower().split('.', 1)
                permission_string = f'{splitted_value[0]}.add_{splitted_value[1]}'
                if self.current_user.has_perm(permission_string) and model['hidden'] is False:
                    return True
            return False

        def get_sections_by_user(self):
            for key in sorted(self.sections.keys()):
                section = {'has_module_perms': False, 'app_label': key, 'app_url': '', 'name': key, 'models': []}
                if check_section_access(self, key):
                    section.update({'has_module_perms': True})
                for m_name in self.sections[key]:
                    app_name, obj_name = m_name['model'].split('.')
                    model = get_model_from_app_list(app_name, obj_name)
                    if model:
                        section['models'].append({"model": model, "hidden": m_name['hidden']})
                if section.get('has_module_perms'):
                    sections_list.append(section)

        get_sections_by_user(self)

        columns = {}
        col = 0
        for sects in self.columns:
            for s in sects:
                for section in sections_list:
                    if section['app_label'] == s:
                        try:
                            columns[col].append(section)
                        except KeyError:
                            columns[col] = [section]
            col += 1
            # Так как сортировка по алфавиту нам не подходит
        return columns

wfm_admin = WfmAdminSite()

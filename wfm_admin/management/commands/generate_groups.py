#
# Copyright 2018 ООО «Верме»
#
# Файл создания групп и прав доступа для секций в административном разделе
#

# coding=utf-8;

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from wfm.settings import ADMIN_SECTIONS


class Command(BaseCommand):
    help = 'Generate section groups and permissions'

    def get_sections(self):
        return ADMIN_SECTIONS

    def get_groups(self):
        return Group.objects.all()

    def get_section_models(self, key):
        sections = self.get_sections()
        for m_name in sections[key]:
            yield m_name

    def get_related_models(self, model):
        fields = apps.get_model(model)._meta.get_fields()
        for field in fields:
            if field.is_relation and field.related_model and not field.one_to_many:
                yield field.related_model

    def get_related_perms(self, model):
        related_models = self.get_related_models(model)
        for rmodel in related_models:
            splitted_name = rmodel._meta.label.lower().split('.', 1)
            yield f"{splitted_name[0]}.change_{splitted_name[1]}"

    def get_model_perms(self, model):
        splitted_name = model.lower().split('.', 1)
        return [
            f"{splitted_name[0]}.add_{splitted_name[1]}",
            f"{splitted_name[0]}.change_{splitted_name[1]}",
            f"{splitted_name[0]}.delete_{splitted_name[1]}"]

    def get_group_by_section(self, section):
        combined_name = f"Управление {section.lower()}"
        group, created = Group.objects.get_or_create(name=combined_name)
        return group, created

    def get_permissions_list(self, section_permissions):
        perm_list = list()
        for perm in section_permissions:
            perm_obj = Permission.objects.filter(codename=perm.split('.')[1]).first()
            if perm_obj:
                perm_list.append(perm_obj)
        return perm_list

    def handle(self, *args, **options):
        for section in self.get_sections():
            section_perms = set()
            for model in self.get_section_models(section):
                model_perms = set()
                model_perms.update(self.get_model_perms(model['model']))
                model_perms.update(list(self.get_related_perms(model['model'])))
                section_perms.update(model_perms)
            group, created = self.get_group_by_section(section)
            if not created:
                group.permissions.clear()
            group.permissions.set(self.get_permissions_list(section_perms))
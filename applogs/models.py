"""
Copyright 2019 ООО «Верме»

Модели приложения applogs
"""
from django.contrib.postgres.fields import JSONField
from django.db import connections, models
from django.db.models import Manager
from django.db.models.query import QuerySet


# Уровни важности
LEVEL_CHOICES = (
    ("INFO", "INFO"),
    ("ERROR", "ERROR"),
    ("DEBUG", "DEBUG"),
    ("WARNING", "WARNING"),
)


class ClientRecord(models.Model):
    message = models.TextField(verbose_name="сообщение")
    user_agent = models.CharField(verbose_name="UserAgent", max_length=512)
    created_at = models.DateTimeField(verbose_name="дата создания", auto_now_add=True)

    class Meta:
        verbose_name = 'Системная ошибки'
        verbose_name_plural = 'Системные ошибки'


class ApproxCountQuerySet(QuerySet):
    def count(self):
        """
        Выводим примерное значение для количества если не применены фильтры
        Предполагается использование Postgres
        """
        if self._result_cache is not None and not self._iter:
            return len(self._result_cache)

        is_filtered = self.query.where or self.query.having
        if is_filtered:
            return super(ApproxCountQuerySet, self).count()
        cursor = connections[self.db].cursor()
        cursor.execute("SELECT reltuples FROM pg_class "
                       "WHERE relname = '%s';" % self.model._meta.db_table)
        return int(cursor.fetchone()[0])


ApproxCountManager = Manager.from_queryset(ApproxCountQuerySet)


class ServerRecord(models.Model):
    headquater = models.CharField(verbose_name='клиент', max_length=255, blank=True, null=True, db_index=True)
    level = models.CharField(verbose_name='важность', max_length=8, choices=LEVEL_CHOICES, default=LEVEL_CHOICES[0][0],
                             blank=False, null=False, db_index=True)
    source = models.CharField(verbose_name='источник', max_length=32, blank=True, null=True, db_index=True)
    method = models.CharField(verbose_name='метод', max_length=64, blank=True, null=True, db_index=True)
    duration = models.FloatField(verbose_name='продолжительность', default=0.0)
    tags = models.CharField(verbose_name='теги', max_length=512, blank=True, null=True)
    message = models.TextField(verbose_name='сообщение')
    params = JSONField(verbose_name='доп. информация', default=None, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='дата создания', auto_now_add=True)

    objects = ApproxCountManager()

    class Meta:
        verbose_name = 'Журнал работы служб'
        verbose_name_plural = 'Журнал работы служб'

    # def created_at_str(self, obj):
    #     """Отображение времени события с секундами"""
    #     return obj.created_at.strftime("%d %b %Y %H:%M:%S")
    # created_at_str.short_description = 'дата создания'

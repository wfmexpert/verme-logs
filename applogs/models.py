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


class CountEstimateManager(Manager):
    def count_estimate(self):
        """
        Выводим примерное значение для количества если не применены фильтры
        Предполагается использование Postgres
        """
        from django.db import connections
        # оборачиваем сырой запрос в кастомную функцию Postgres
        raw_sql = self.get_queryset().query.__str__()
        with connections[self.db].cursor() as cursor:
            cursor.execute(f"""
            SELECT count_estimate( {raw_sql} );
            """)
            fetched_result = cursor.fetchone()
            count_estimate = fetched_result[0] if fetched_result else None

        if count_estimate is not None and count_estimate > 5000:
            return count_estimate

        return self.get_queryset().count()
        # cursor.execute("SELECT reltuples FROM pg_class "
        #                "WHERE relname = '%s';" % self.model._meta.db_table)
        # return int(cursor.fetchone()[0])


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

    objects = CountEstimateManager()

    class Meta:
        verbose_name = 'Журнал работы служб'
        verbose_name_plural = 'Журнал работы служб'

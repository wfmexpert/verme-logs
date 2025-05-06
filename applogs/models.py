"""
Copyright 2019 ООО «Верме»

Модели приложения applogs
"""
from django.contrib.auth import get_user_model
from django.db import connections, models
from django.db.models import Manager
from django.db.models.query import QuerySet

try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

    
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
    username = models.CharField(verbose_name="Пользователь", max_length=512, null=True, blank=True,)
    headers = JSONField(verbose_name="Заголовок запроса", default=None, null=True, blank=True)

    class Meta:
        verbose_name = "Системная ошибка"
        verbose_name_plural = "Системные ошибки"


class CountEstimateQuerySet(QuerySet):
    def count_estimate(self):
        """
        Выводим примерное значение для количества если не применены фильтры
        Предполагается использование Postgres
        """
        from django.db import connections

        # оборачиваем сырой запрос в кастомную функцию Postgres
        # Получаем запрос и параметры
        sql, sql_params = self.query.get_compiler(using=self.db).as_sql()
        # Так как в результате у нас будут вложенные одиночные кавычки, эскейпим параметры в формате PostgreSQL
        sql_params_escaped = tuple(f"''{param}''" for param in sql_params)
        # as_sql() вернул sql, отформатированный через "%", форматируем
        sql_inner_formatted = sql % sql_params_escaped

        with connections[self.db].cursor() as cursor:
            cursor.execute("select exists(select * from pg_proc where proname = 'count_estimate');")
            exists = cursor.fetchone()[0]
            if not exists:
                cursor.execute("""
                    CREATE FUNCTION count_estimate(query text) RETURNS integer AS
                    $func$
                    DECLARE
                        rec   record;
                        rows  integer;
                    BEGIN
                        FOR rec IN EXECUTE 'EXPLAIN ' || query LOOP
                            rows := substring(rec."QUERY PLAN" FROM ' rows=([[:digit:]]+)');
                            EXIT WHEN rows IS NOT NULL;
                        END LOOP;
                    
                        RETURN rows;
                    END
                    $func$ LANGUAGE plpgsql;
                """)

            cursor.execute(f"SELECT count_estimate( ' {sql_inner_formatted} ' );")
            fetched_result = cursor.fetchone()
            count_estimate = fetched_result[0] if fetched_result else None

        if count_estimate is not None and count_estimate > 1000:
            return count_estimate

        return self.count()


class ServerRecord(models.Model):
    headquater = models.CharField(verbose_name="клиент", max_length=255, blank=True, null=True, db_index=True)
    level = models.CharField(verbose_name="важность", max_length=8, choices=LEVEL_CHOICES, default=LEVEL_CHOICES[0][0], blank=False, null=False, db_index=True,)
    source = models.CharField(verbose_name="источник", max_length=32, blank=True, null=True, db_index=True)
    method = models.CharField(verbose_name="метод", max_length=64, blank=True, null=True, db_index=True)
    duration = models.FloatField(verbose_name="продолжительность", default=0.0)
    tags = models.CharField(verbose_name="теги", max_length=512, blank=True, null=True, db_index=True)
    message = models.TextField(verbose_name="сообщение")
    params = JSONField(verbose_name="доп. информация", default=None, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="дата создания", auto_now_add=True, db_index=True)
    request = models.TextField(verbose_name="текст запроса", blank=True, null=True)

    objects = CountEstimateQuerySet.as_manager()

    class Meta:
        verbose_name = "Журнал работы служб"
        verbose_name_plural = "Журнал работы служб"

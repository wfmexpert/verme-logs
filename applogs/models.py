from django.contrib.postgres.fields import JSONField
from django.db import models

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


class ServerRecord(models.Model):
    headquater = models.CharField(verbose_name='клиент', max_length=255, blank=True, null=True)
    level = models.CharField(verbose_name='важность', max_length=8, choices=LEVEL_CHOICES, default=LEVEL_CHOICES[0][0],
                             blank=False, null=False)
    source = models.CharField(verbose_name='источник', max_length=32, blank=True, null=True)
    method = models.CharField(verbose_name='метод', max_length=64, blank=True, null=True)
    duration = models.FloatField(verbose_name='продолжительность', default=0.0)
    tags = models.CharField(verbose_name='теги', max_length=512, blank=True, null=True)
    message = models.TextField(verbose_name='сообщение')
    params = JSONField(verbose_name='доп. информация', default=None, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Журнал работы служб'
        verbose_name_plural = 'Журнал работы служб'

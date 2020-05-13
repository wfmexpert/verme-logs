Логирование предполагает возможность экспорта записей через действия, приложение `applogs` требует для работы приложение`xlsexport`.

Приложение `applogs` пишет логи в отдельную базу `app_logs`, которую нужно предварительно создать.
```
sudo su - postgres -c 'createdb app_logs'
sudo su - postgres -c 'psql -t postgres -c "GRANT ALL PRIVILEGES ON DATABASE app_logs to wfm"'
```

Далее необходимо внести изменения в settings.py, добавив соответствующий роутер (`'applogs.db_router.LogsDBRouter'`) в секцию роутеров

пример:
```
DATABASE_ROUTERS = [
    'wfm.default_db_router.DefaultDBRouter',
    'applogs.db_router.LogsDBRouter',
]
```
изменить роутер по умолчанию `wfm/db_router.py`, добавив `app_logs` в IGNORED_APPS

пример:
```
# coding=utf-8;


class DefaultDBRouter():

    IGNORED_APPS = ('applogs',)

    def is_ignored_app(self, obj):
        return obj._meta.app_label in self.IGNORED_APPS

    def db_for_read(self, model, **hints):
        if self.is_ignored_app(model):
            return None
        return 'default'

    def db_for_write(self, model, **hints):
        if self.is_ignored_app(model):
            return None
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if self.is_ignored_app(obj1) or self.is_ignored_app(obj2):
            return None
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.IGNORED_APPS and db == 'default':
            return False

        if app_label in self.IGNORED_APPS and db != 'default':
            return True
        if db != 'default':
            return False
        return True

```

класс фильтра логов

пример:
```
class F(logging.Filter):
    """ Этот "фильтр" не фильтрует, а добавляет в объекты record айпи и имя
        юзера, делающего запрос, чтоб форматтер их вставил потом в строку """
    def filter(self, record):
        # TODO: похоже, это всё больше не работает, потому что вместо request'а тут какой-то socket
        request = getattr(record, 'request', None)

        if request and hasattr(request, 'user'):  # user
            record.user = request.user
        else:
            record.user = '--'

        if request and hasattr(request, 'META'):  # IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                record.ip = x_forwarded_for.split(',')[-1]
            else:
                record.ip = request.META.get('REMOTE_ADDR')
        else:
            record.ip = '--'

        return True
```
блок `LOGGING` с указанием обработчика (`'applogs.handlers.DBLogsHandler'`)

пример:
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'main': {
            '()': F
        }
    },
    'formatters': {
        'stamp': {
            'format': '%(levelname)s [%(asctime)s] %(ip)s "%(user)s" %(name)s.%(module)s %(message)s'
        },
    },
    'handlers': {
        'file_main': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'main.log'),
            'formatter': 'stamp',
            'filters': ['main'],
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'stamp',
            'filters': ['main'],
        },
        'db': {
            'class': 'applogs.handlers.DBLogsHandler',
            'filters': ['main'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_main', 'console'],
            'level': 'WARNING',
        },
        'apps': {
            'handlers': ['file_main', 'console'],
            'level': 'DEBUG',
        },
        'command': {
            'handlers': ['db', 'console'],
            'level': 'DEBUG',
        },
        'api': {
            'handlers': ['db', 'console'],
            'level': 'DEBUG',
        },
        'remote_service': {
            'handlers': ['db', 'console'],
            'level': 'DEBUG',
        },
    },
}
```
а также указать дополнительную базу `applogs` в секцию `DATABASES` файла `settings_local.py`
пример:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('WFM_DB_HOST', '127.0.0.1'),
        'NAME': os.environ.get('WFM_DB_NAME', 'out_db'),
        'USER': os.environ.get('WFM_DB_USER', 'wfm'),
        'PASSWORD': os.environ.get('WFM_DB_PASSWORD', 'wfm'),
    },
    'applogs': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('WFM_DB_HOST', '127.0.0.1'),
        'NAME': 'app_logs',
        'USER': os.environ.get('WFM_DB_USER', 'wfm'),
        'PASSWORD': os.environ.get('WFM_DB_PASSWORD', 'wfm'),
    },
}

```
Внести изменения в `urls.py`, добавив в :
```
urlpatterns = [
...
url(r'^applogs/',       include('applogs.urls')),
...
]
```
Далее необходимо перезапустить портал и выполнить миграции приложения, и добавить их выполнение в verme.update
```
sudo initctl restart outsourcing (wfmportal, vision)
WFM_DB_PASSWORD=<пароль к БД> ./manage.py migrate applogs --database applogs
```
# from datetime import timedelta
from logging import Handler


class DBLogsHandler(Handler):
    def emit(self, record):
        # логгер настраивается до настройки app'ов, так что если перенести
        # импорт в начало файла, всё упадёт
        from .models import ServerRecord
        msg = record.msg
        if len(record.args) > 0:
            msg = msg % record.args

        params = getattr(record, 'params', None)
        headquater = getattr(record, 'headquater', None)
        source = getattr(record, 'source', None)
        method = getattr(record, 'method', None)
        duration = getattr(record, 'duration', 0.0)
        tags = getattr(record, 'tags', '')

        if params:
            if not source:
                source = params.get('source', '--')
            if not method:
                method = params.get('method', '--')
            if not headquater:
                headquater = params.get('user', '--')

        ServerRecord.objects.create(level=record.levelname,
                                    message=msg,
                                    params=params,
                                    headquater=headquater,
                                    source=source,
                                    method=method,
                                    duration=duration,
                                    tags=tags
                                    )

        # Тут используется параллельное подключение к базе.
        # Если использовать основное:
        # Может случиться так, что эта запись будет добавлена в транзакции,
        # а потом транзакция будет отменена, и никакого лога не будет.
        # В качестве не очень чистого хака можно попробовать:
        # from django.conf import settings
        # from django.db.utils import ConnectionHandler
        # connections = ConnectionHandler(settings.DATABASES)
        # connection = connections['default']
        # cur = connection.cursor()
        # cur.execute("INSERT INTO ...")
        # cur.close()
        # http://stackoverflow.com/questions/11554844/do-cursors-in-django-run-inside-the-open-transaction

Пакет состоит из приложений:
* `applogs` - логирование
* `xlsexport` - импорт/экспорт в XLSX/XLSX
* `wfm_admin` - панель администратора (определяется конфигурационным файлом wfm_admin.py)
Для использования, необходимо добавить эти приложения в INSTALLED_APPS, при этом `wfm_admin` должен быть указан последним.

При этом нужно убедиться что установлены пакеты `xlswriter`, `xlwt` и `xlrd`.

Для wfm_admin дополнительно добавить в `urls.py`:
```
from wfm_admin.admin import wfm_admin
urlpatterns = [
    ...
    url(r'^admin/', wfm_admin.urls),
    ...
]
```

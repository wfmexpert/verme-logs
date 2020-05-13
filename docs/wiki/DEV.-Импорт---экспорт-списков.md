Импорт/экспорт из XLSX/XLS файлов реализован приложением xlsexport.
Для использования функционала необходимо:
1. Убедиться что установлены зависимости - `xlswriter`, `xlwt` и `xlrd`.
2. Добавить `xlsexport` в `INSTALLED_APPS`
3. Для вывода в секции в админке добавить:
* `'xlsexport.ExportTemplate'` - шаблоны, используемый при импорте/экспорте;
* `'xlsexport.ImportTemplate'` - страница импорта из файлов
4. Добавить url приложнения в `urls.py`:
```
urlpatterns = [
...
url(r'^xlsexport/',     include(('xlsexport.urls', 'xlsexport'), namespace='xlsexport')),
...
]
```

В интерфейсе пользователя выгрузка отчетов может быть реализована с помощью вызова функции, в которую передается уникальный код отчета и queryset(опционально). Функция вернет объект HTTPResponse с файлом или же JSONReponse с описанием ошибки (например, если отчет с указанным кодом не существует). Если queryset не передан, он будет определен на основании описания шаблона.
пример:
```
from xlsexport.methods import get_report_by_code
return get_report_by_code('claim', query_set)
```

Для экспорта аналогично, необходимо получить шаблон по коду и передать ему файл.
пример:
```
from xlsexport.methods import get_template_by_code
template = get_template_by_code('quota')
errors = template.to_import(xls)
```
При успешном выполнении функция не возвращает ничего (None). В случае, если при импорте возникнут ошибки, они будут переданы в массив errors и доступны для вывода. 
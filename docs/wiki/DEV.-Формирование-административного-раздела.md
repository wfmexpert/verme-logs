В файле конфигурации описываются секции и модели, которые должны быть отображены в этой секции, формат:
{"model": 'имя_приложения.имя_модели', "hidden": True/Fasle}

Флаг `hidden` определяет будет ли пункт отображен в секции в административном разделе. 
Если `hidden=True`, то пункт отображен не будет, но при запуске формирования групп и прав доступа, для данной модели будут созданы соответствующие права доступа `add/change/delete`.

Пример файла конфигурации `wfm_admin.py`:

```
ADMIN_SECTIONS = {

    'СИСТЕМНЫЕ':        [{"model": 'remotes.RemoteService', "hidden": False}, {"model": 'notifications.NotifyItem', "hidden": False}, {"model": 'permission.Page', "hidden": False}, {"model": 'xlsexport.ExportTemplate', "hidden": False}, {"model": 'xlsexport.ImportTemplate', "hidden": False}],

    'ЖУРНАЛЫ':          [{"model": 'applogs.ClientRecord', "hidden": False}, {"model": 'applogs.ServerRecord', "hidden": False}],

    'ДОСТУП':           [{"model": 'permission.AccessRole', "hidden": False}, {"model": 'permission.AccessProfile', "hidden": False}, {"model": 'auth.User', "hidden": False}, {"model": 'auth.Group', "hidden": False}, {"model": 'authtoken.Token', "hidden": False}],

    'КОМПАНИИ':         [{"model": 'outsource.Headquater', "hidden": False}, {"model": 'outsource.Organization', "hidden": False}, {"model": 'outsource.Agency', "hidden": False}, {"model": 'outsource.OrgLink', "hidden": False}],

    'СОТРУДНИКИ':       [{"model": 'outsource.Job', "hidden": False}, {"model": 'employees.DocType', "hidden": False}, {"model": 'employees.AgencyEmployee', "hidden": False}, {"model": 'employees.EmployeeEvent', "hidden": False}, {"model": 'employees.EmployeeHistory', "hidden": False},
                         {"model": 'employees.JobHistory', "hidden": True}, {"model": 'employees.OrgHistory', "hidden": True}, {"model": 'employees.EmployeeDoc', "hidden": True}],

    'ЗАПРОСЫ НА ПЕРСОНАЛ':  [{"model": 'shifts.OutsourcingRequest', "hidden": False}],

    'ПРОМОУТЕРЫ':       [{"model": 'outsource.StoreArea', "hidden": False}, {"model": 'outsource.QuotaVolume', "hidden": False}, {"model": 'outsource.Quota', "hidden": False}, {"model": 'shifts.PromoShift', "hidden": False}],

    'ПРЕТЕНЗИИ':        [{"model": 'claims.ClaimRequest', "hidden": False}, {"model": 'claims.ClaimType', "hidden": False}, {"model": 'claims.ClaimStatus', "hidden": False}, {"model": 'claims.ClaimAction', "hidden": False}],
}
ADMIN_COLUMNS = [
    ('СИСТЕМНЫЕ', 'ЖУРНАЛЫ', 'ДОСТУП'),
    ('КОМПАНИИ', 'СОТРУДНИКИ', 'ЗАПРОСЫ НА ПЕРСОНАЛ', 'ПРОМОУТЕРЫ', 'ПРЕТЕНЗИИ'),
]
```
Далее необходимо внести изменения в `urls.py`:
```
from wfm_admin.admin import wfm_admin
url(r'^admin/',          wfm_admin.urls),
```
# Запуск формирования прав доступа
```
WFM_DB_PASSWORD=<пароль к БД> ./manage.py generate_groups
```
После запуска, если группа для секции уже существует, то права доступа для секции будут обновлены, если группа отсутствует, то она будет создана автоматически с соответствующими правами доступа.

Права доступа `add/change/delete` создаются для всех моделей описанных в секции, для зависимых моделей (например определяемых FK ключом из модели описанной в секции) создаются дополнительно права доступа `change`.
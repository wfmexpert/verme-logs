=====
verme-logs
=====

Система журналирования серверных процессов и
сбора информации об ошибках на стороне браузера

Quick start
-----------

1. Add "applogs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'applogs',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('applogs/', include('applogs.urls')),

3. Run `python manage.py migrate` to create applogs models.

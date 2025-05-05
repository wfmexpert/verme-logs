from . import admin
try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url


urlpatterns = [
    url(r'^xls_export/$', admin.xls_export_view, name='xls_export_view'),
]

from . import admin
from django.urls import re_path


urlpatterns = [
    re_path(r'^xls_export/$', admin.xls_export_view, name='xls_export_view'),
]

from . import admin
from django.conf.urls import url


urlpatterns = [
    url(r'^xls_export/$', admin.xls_export_view, name='xls_export_view'),
]

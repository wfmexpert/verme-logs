from . import views, admin
from django.urls import re_path

urlpatterns = [
    re_path(r'^$', views.CreateView.as_view(), name='create'),
    re_path(r'^admin/delete_old_serverrecords$', admin.delete_old_server_records_view, name='admin_delete_old_serverrecords'),
    re_path(r'^admin/delete_all_clientrecords$', admin.delete_all_client_records_view, name='admin_delete_all_clientrecords'),
]

from . import views, admin
try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url

urlpatterns = [
    url(r'^$', views.CreateView.as_view(), name='create'),
    url(r'^admin/delete_old_serverrecords$', admin.delete_old_server_records_view, name='admin_delete_old_serverrecords'),
    url(r'^admin/delete_all_clientrecords$', admin.delete_all_client_records_view, name='admin_delete_all_clientrecords'),
]

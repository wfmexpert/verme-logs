from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r'^meta$', views.meta_view, name='metadata'),
    re_path(r'^begin$', views.auth_view, name='begin'),
    re_path(r'^asc$', views.complete_view, name='complete'),
    re_path(r'^slo$', views.logout_view, name='logout'),
    re_path(r'^error$', views.error_view, name='error'),
]

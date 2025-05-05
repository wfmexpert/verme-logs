try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url

from . import views


urlpatterns = [
    url(r'^meta$', views.meta_view, name='metadata'),
    url(r'^begin$', views.auth_view, name='begin'),
    url(r'^asc$', views.complete_view, name='complete'),
    url(r'^slo$', views.logout_view, name='logout'),
    url(r'^error$', views.error_view, name='error'),
]

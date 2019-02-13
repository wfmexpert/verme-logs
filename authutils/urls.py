from django.urls import path, include

from . import views


urlpatterns = [
    path('saml/', include(('apps.authutils.saml.urls', 'saml'), namespace='saml')),
    path('admin/login/', views.admin_login_view, name='admin_login'),
]

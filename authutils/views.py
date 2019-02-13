from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from django.contrib.admin.sites import AdminSite

site = AdminSite()
site.login_template = 'admin/login_form.html'

@ensure_csrf_cookie
def admin_login_view(request):
    extra_context = {
        'saml_idps': getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', {})
    }
    return site.login(request, extra_context=extra_context)

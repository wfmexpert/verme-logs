import base64
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.contrib.admin.sites import AdminSite

from onelogin.saml2 import compat
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML
from social_core.actions import do_auth, do_complete
from social_django.utils import load_backend, load_strategy, psa
from social_django.views import _do_login
from .methods import set_user_login_details



def with_saml_backend(func):
    """ Деократор @psa ожидает, что вместе с реквестом из url'ов придёт аргумент backend="saml",
        но тут ссылки переопределены, и аргумента не будет. Так что добавляем его. """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return func(request, 'saml', *args, **kwargs)
    return wrapper


def meta_view(request):
    complete_url = reverse('authutils:saml:complete')
    saml_backend = load_backend(
        load_strategy(request),
        "saml",
        redirect_uri=complete_url,
    )
    metadata, errors = saml_backend.generate_metadata_xml()
    if not errors:
        return HttpResponse(content=metadata, content_type='text/xml')


def error_view(request):
    storage = messages.get_messages(request)
    storage.used = True
    err_type = request.GET.get('type')
    if err_type == 'login-error':
        messages.error(request, "Пользователь не имеет доступа к системе.")
    elif err_type == 'inactive-user':
        messages.error(request, "Пользователь заблокирован.")
    return HttpResponseRedirect(reverse('login'))


# Дальше аналоги вьюх из social_auth/views.py
@never_cache
@with_saml_backend
@psa('/saml/asc')  # тот же путь, что и у complete_view, иначе будте ошибка CSRF
def auth_view(request, backend, *args, **kwargs):
    return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)


@never_cache
@csrf_exempt
@with_saml_backend
@psa('/saml/asc')
def complete_view(request, backend, *args, **kwargs):
    # Check if ADFS doesn't allow access to the Service
    if 'SAMLResponse' in request.POST:
        print('SAMLResponse IS in request.POST')
        saml_response_encoded = request.POST['SAMLResponse']
        saml_response_string = base64.b64decode(saml_response_encoded).decode('utf-8')

        if 'samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:RequestDenied"' in saml_response_string:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, "Пользователь не имеет доступа к системе. Убедитесь в том, что пользователю присвоены права доступа в ADFS.")
            return HttpResponseRedirect(reverse('admin:login'))

    # Если в системе залогинен один пользователь, а другой пытается залогиниться,
    # social auth кинет из пайплайна эксепшен об этом. Если пайплайн переопределить
    # и убрать эксепшен, вход вообще не будте работать, потому что do_complete
    # при виде влогиненного request_user'а просто не вызывает login для нового.
    # Так что...
    # Говорим social auth'у, что в рекветсе не было пользователя, так всё вроде ок.
    request_user = None  # request.user
    set_user_login_details(request, 'SAML', True)
    return do_complete(request.backend, _do_login, request_user,
                       redirect_name=REDIRECT_FIELD_NAME, request=request,
                       *args, **kwargs)


@never_cache
@with_saml_backend
@psa()
@csrf_protect
def logout_view(request, *args, **kwargs):
    backend = request.backend
    logout(request)

    # Пользователя разлогинили, теперь нужно ответить провайдеру.
    # Для начала нужно узнать, от какого именно IdentityProvider'а пришёл запрос.
    # Как минимму OneLogin не присылает в запросе никаких опознавательных знаков кроме атрибута Issuer.
    # В Issuer у него находится путь к его метадате. В конфиге тот же путь надо указать в entity_id.

    # вынимаем значение Issuer
    request_str = compat.to_string(OneLogin_Saml2_Utils.decode_base64_and_inflate(request.GET['SAMLRequest']))
    xml_doc = OneLogin_Saml2_XML.to_etree(request_str)
    issuer_nodes = OneLogin_Saml2_XML.query(xml_doc, '/samlp:LogoutRequest/saml:Issuer')
    if len(issuer_nodes) == 0:
        raise ValueError('no Issuer in logout request: ' + request_str)
    issuer = issuer_nodes[0].text

    # ищем имя IDP
    idp_configs = backend.setting('ENABLED_IDPS')
    idp_name = next((name for name, cfg in idp_configs.items() if cfg.get('entity_id') == issuer), None)
    if idp_name is None:
        raise ValueError(f"IDP not found for Issuer '{issuer}' in logout request: " + request_str)

    # формируем адрес редиректа
    idp = backend.get_idp(idp_name)
    if idp.slo_config == {}:  # если конфига slo нет
        url = settings.LOGOUT_REDIRECT_URL
    else:
        url = backend._create_saml_auth(idp, remove_signature_from_get=True).process_slo()

    return HttpResponseRedirect(url)


# Custom admin login view (with button for authentication via ADFS)
site = AdminSite()
site.login_template = 'admin/login_form.html'


@ensure_csrf_cookie
def admin_login_view(request):
    extra_context = {
        'saml_idps': getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', {})
    }
    return site.login(request, extra_context=extra_context)

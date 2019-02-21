from django.contrib.auth.models import User
from social_core.exceptions import AuthException
from apps.authutils.methods import create_or_update_employee
import uuid


def associate_by_name_id(backend, details, response, request, user=None, *args, **kwargs):
    """ Этот пайплайн занимается поиском пользователя по nameId в зависимости от параметра name_id_type из конфига """
    idp = backend.get_idp(response['idp_name'])
    name_id_type = idp.conf['name_id_type']
    name_id = response['attributes']['name_id']
    request.session['saml:nameid'] = name_id

    # Дополнительные параметры на основе IDP
    saml_superuser_ou = idp.conf.get('verme_superuser_ou', None)
    saml_create_user_employee = idp.conf.get('verme_create_user_employee', False)
    saml_update_user = idp.conf.get('verme_update_user', False)
    saml_update_employee = idp.conf.get('verme_update_employee', False)

    kwargs = None
    if name_id_type == 'username':
        kwargs = {'username': name_id}
    elif name_id_type == 'number':
        kwargs = {'employee__number': name_id}
    elif name_id_type == 'phone':
        kwargs = {'employee__notify_phone': name_id}
    else:  # email по умолчанию
        kwargs = {'email': name_id}

    users = list(User.objects.filter(**kwargs))
    params = response['attributes']

    # Если не нашли пользователя
    if len(users) == 0:
        # Если включено создание пользователя
        if saml_create_user_employee:
            user = create_or_update_employee(backend, saml_superuser_ou, **params)
        else:
            return None
    # Если нашли пользователя
    if len(users) == 1:
        # Если включено обновление пользователя
        if saml_update_user:
            user = create_or_update_employee(backend, saml_superuser_ou, saml_update_user, saml_update_employee, users[0], **params)
        else:
            user = users[0]
    # Если нашли несколько пользователей
    if len(users) > 1:
        raise AuthException(backend, f'Parameters {kwargs} are associated multiple users')
    return {'user': user, 'is_new': False}

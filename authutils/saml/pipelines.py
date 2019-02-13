from django.contrib.auth.models import User
from social_core.exceptions import AuthException
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

    kwargs = None
    if name_id_type == 'username':
        kwargs = {'username': name_id}
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
            user = create_or_update_employee(backend, saml_superuser_ou, saml_update_user, users[0], **params)
        else:
            user = users[0]
    # Если нашли несколько пользователей
    if len(users) > 1:
        raise AuthException(backend, f'Parameters {kwargs} are associated multiple users')
    return {'user': user, 'is_new': False}


def create_or_update_employee(backend, saml_superuser_ou, saml_update_user=False, user=None, **kwargs):

    default = kwargs.get('name_id', None)
    dn = kwargs.get('DN', None)

    # Если основные параметры не найдены
    # выходим
    if not default or not dn:
        return None

    # Получаем атрибуты из запроса
    username = kwargs.get('username', default)
    email = kwargs.get('EMail', None)

    if email:
        email = email[0]
    else:
        email = default

    first_name = kwargs.get('FirstName', None)
    if not first_name:
        message = 'Не передан параметр FirstName'
        raise AuthException(backend, message)
    else:
        first_name = first_name[0]

    last_name = kwargs.get('LastName', None)
    if not last_name:
        message = 'Не передан параметр LastName'
        raise AuthException(backend, message)
    else:
        last_name = last_name[0]

    # Берем первый OU из DN
    ou = dn[0].split(',OU=')[1].split(',OU=')[0]
    if ou == saml_superuser_ou:
        is_superuser = True
    else:
        is_superuser = False

    # Если сотрудника нет
    # то создаем
    if not user:
        # Создаем рандомный пароль
        password = str(uuid.uuid4())
        if is_superuser:
            user = User.objects.create_superuser(username=username,
                                                 email=email,
                                                 first_name=first_name,
                                                 last_name=last_name,
                                                 password=password)
        else:
            user = User.objects.create_user(username=username,
                                            email=email,
                                            first_name=first_name,
                                            last_name=last_name,
                                            password=password)
        return user
    # Если сотрудник есть
    # то обновляем
    else:
        if saml_update_user:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            if is_superuser:
                user.is_superuser = True
                user.is_staff = True
            else:
                user.is_superuser = False
                user.is_staff = False
            user.save()
        return user

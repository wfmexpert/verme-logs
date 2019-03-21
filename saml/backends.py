from onelogin.saml2.auth import OneLogin_Saml2_Auth
from social_core.backends.saml import OID_USERID, SAMLAuth, SAMLIdentityProvider
from ratelimitbackend.backends import RateLimitMixin


class SAMLIdentityProviderExt(SAMLIdentityProvider):
    """ Кастомный IdentityProvider.
        Исправляет использование атрибута name_id.
        Добавляет 'singleLogoutService' к конфигу. """

    def get_user_permanent_id(self, attributes):
        """ Если значение атрибута - строка, возвращает её как есть,
            иначе возвращает первый элемент (там должен быть список).
            Оригинальный метод возвращает всегда первый элемент, что некорректно для строк (например name_id). """
        value = attributes[self.conf.get('attr_user_permanent_id', OID_USERID)]
        return value if isinstance(value, str) else value[0]

    @property
    def slo_config(self):
        return self.conf.get('slo', {})

    @property
    def saml_config_dict(self):
        """ Добавляет параметры SLO из конфига. """
        cfg = super().saml_config_dict
        cfg['singleLogoutService'] = self.slo_config
        return cfg


class SAMLAuthExt(RateLimitMixin, SAMLAuth):
    """ Кастомный auth backend. Возвращает переопределённый IdentityProvider. """
    def get_idp(self, idp_name):
        idp_config = self.setting('ENABLED_IDPS')[idp_name]
        return SAMLIdentityProviderExt(idp_name, **idp_config)

    def _create_saml_auth(self, idp, remove_signature_from_get=False):
        """ Добавляет возможность удалить 'Signature' из параметров,
            https://github.com/wfmexpert/wfmportal/issues/1111 """
        get_data = self.strategy.request_get()
        if remove_signature_from_get:
            get_data.pop('Signature', None)

        config = self.generate_saml_config(idp)
        request_info = {
            'https': 'on' if self.strategy.request_is_secure() else 'off',
            'http_host': self.strategy.request_host(),
            'script_name': self.strategy.request_path(),
            'server_port': self.strategy.request_port(),
            'get_data': get_data,
            'post_data': self.strategy.request_post(),
        }
        return OneLogin_Saml2_Auth(request_info, config)

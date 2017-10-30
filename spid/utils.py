# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import get_user_model, login
from .apps import SpidConfig
from .saml import SpidSaml2Auth

from onelogin.saml2.settings import OneLogin_Saml2_Settings

User = get_user_model()

ATTRIBUTES_MAP = {
    'familyName': 'last_name',
    'name': 'first_name'
}


def prepare_django_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        'server_port': request.META['SERVER_PORT'],
        'get_data': request.GET.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'post_data': request.POST.copy()
    }
    return result


def process_user(request, attributes):
    from .app_settings import app_settings
    attrs = {}
    try:
        for attr in attributes:
            if attr in app_settings.REQUESTED_ATTRIBUTES:
                key = ATTRIBUTES_MAP.get(attr, attr)
                attrs[key] = attributes[attr][0]
        user, __ = User.objects.get_or_create(
            **attrs
        )
        user.is_active = True
        login(request, user)
        return user
    except (KeyError, ValueError):
        return


def init_saml_auth(request, idp):
    from .app_settings import app_settings
    config = {
        'request_data': request
    }
    if idp == 'test':
        config['old_settings'] = OneLogin_Saml2_Settings(custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    else:
        config['old_settings'] = SpidConfig.get_saml_settings(idp)
    auth = SpidSaml2Auth(
        **config
    )
    return auth

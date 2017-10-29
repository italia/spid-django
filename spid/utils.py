# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import get_user_model, login
from .saml import SpidSaml2Auth

User = get_user_model()


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
    try:
        email = attributes['email'][0]
        first_name = attributes['name'][0]
        last_name = attributes['familyName'][0]

        user, __ = User.objects.get_or_create(
            email=email, username=email,
            first_name=first_name, last_name=last_name
        )
        user.is_active = True
        login(request, user)
        return user
    except (KeyError, ValueError):
        return


def init_saml_auth(req):
    auth = SpidSaml2Auth(req, custom_base_path=settings.SAML_FOLDER)
    return auth

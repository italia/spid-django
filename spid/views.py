# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import (HttpResponse, HttpResponseRedirect, HttpResponseServerError)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_POST, require_http_methods

from .saml import SpidSaml2Auth
from .utils import init_saml_auth, process_user, prepare_django_request
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils


@require_POST
def login(request):
    """
        Handle login action ( SP -> IDP )
    """
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    args = []
    if 'idp' in req['post_data']:
        if 'next' in req['get_data']:
            args.append(req['get_data'].get('next'))
        return HttpResponseRedirect(auth.login(*args))
    return HttpResponseServerError()


def slo_logout(request):
    """
        Logout
        Handle SLO ( SP -> IDP )
    """
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    name_id = None
    session_index = None
    if 'samlNameId' in request.session:
        name_id = request.session['samlNameId']
    if 'samlSessionIndex' in request.session:
        session_index = request.session['samlSessionIndex']
    return HttpResponseRedirect(
        auth.logout(
            name_id=name_id,
            session_index=session_index,
        )
    )


def sls_logout(request):
    """
        Logout
        Handle SLS ( IDP -> SP )
    """
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False
    dscb = lambda: request.session.flush()
    url = auth.process_slo(delete_session_cb=dscb)
    errors = auth.get_errors()
    redirect_to = '/'
    if len(errors) == 0:
        if url is not None:
            redirect_to = url
        else:
            success_slo = True
            django_logout(request)
    return HttpResponseRedirect(redirect_to)


def attributes_consumer(request):
    """
        Consume attributes from IDP
        ( IDP -> SP )
    """
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    auth.process_response()
    errors = auth.get_errors()
    if not errors:
        user_attributes = auth.get_attributes()
        process_user(request, user_attributes)
        user_attributes = auth.get_attributes()
        request.session['samlUserdata'] = user_attributes
        request.session['samlNameId'] = auth.get_nameid()
        request.session['samlSessionIndex'] = auth.get_session_index()
        redirect_to = '/'
        if 'RelayState' in req['post_data'] and OneLogin_Saml2_Utils.get_self_url(req) != req['post_data']['RelayState']:
            redirect_to = auth.redirect_to(req['post_data']['RelayState'])
        return HttpResponseRedirect(redirect_to)
    return HttpResponseServerError()


def metadata(request):
    """
        Expose SP Metadata
    """
    saml_settings = OneLogin_Saml2_Settings(
        settings=None,
        custom_base_path=settings.SAML_FOLDER,
        sp_validation_only=True
    )
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp

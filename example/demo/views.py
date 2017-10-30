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


def attrs(request):
    paint_logout = False
    attributes = False

    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()

    return render_to_response('attrs.html',
                              context=RequestContext(
                                    request,
                                    {
                                        'request': request,
                                        'paint_logout': paint_logout,
                                        'attributes': attributes
                                    }
                             ).flatten()
    )

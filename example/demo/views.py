# -*- coding: utf-8 -*-
from django.urls import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext


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

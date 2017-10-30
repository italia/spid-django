# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import attrs
admin.autodiscover()


urlpatterns = [
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'^attrs/$', attrs, name='attrs'),
    url(r'^spid/', include('spid.urls')),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
]

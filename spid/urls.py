# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import attributes_consumer, login, metadata, slo_logout, sls_logout


app_name = 'spid'

urlpatterns = [
    url(r'^attributes-consumer/$', attributes_consumer, name='attributes-consumer'),
    url(r'^metadata/$', metadata, name='metadata'),
    url(r'^login/$', login, name='login'),
    url(r'^slo-logout/$', slo_logout, name='slo-logout'),
    url(r'^sls-logout/$', sls_logout, name='sls-logout'),
]

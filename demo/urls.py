# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import attributes_consumer, attrs, logout, login, metadata
admin.autodiscover()

urlpatterns = [
    url(r'^attrs$', attrs, name='attrs'),
    url(r'^attributes-consumer$', attributes_consumer, name='attributes-consumer'),
    url(r'^metadata$', metadata, name='metadata'),
    url(r'^login$', login, name='login'),
    url(r'^logout$', logout, name='logout'),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
]

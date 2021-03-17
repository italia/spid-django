from django.urls import path

from .conf import settings
from . import views


SPID_URLS_PREFIX = settings.SPID_URLS_PREFIX

urlpatterns = [
    path(f'{SPID_URLS_PREFIX}', views.index, name='index'),
    path(f'{SPID_URLS_PREFIX}echo_attributes', views.EchoAttributesView.as_view(), name='spid_echo_attributes'),

    path(f'{SPID_URLS_PREFIX}login', views.spid_login, name='spid_login'),
    path(f'{SPID_URLS_PREFIX}logout', views.spid_logout, name='spid_logout'),
    path(f'{SPID_URLS_PREFIX}metadata', views.metadata_spid, name='spid_metadata'),

    path(f'{SPID_URLS_PREFIX}acs', views.AssertionConsumerServiceView.as_view(), name='saml2_acs'),
    path(f'{SPID_URLS_PREFIX}ls', views.LogoutView.as_view(), name='saml2_ls'),
    path(f'{SPID_URLS_PREFIX}ls/post', views.LogoutView.as_view(), name='saml2_ls_post')
]

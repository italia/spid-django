from django.urls import path
from djangosaml2_spid import views


SAML2_URL_PREFIX = 'spid/'

urlpatterns = [
    path(f'{SAML2_URL_PREFIX}', views.index, name='index'),
    path(f'{SAML2_URL_PREFIX}echo_attributes', views.EchoAttributesView.as_view(), name='spid_echo_attributes'),

    path(f'{SAML2_URL_PREFIX}login', views.spid_login, name='spid_login'),
    path(f'{SAML2_URL_PREFIX}logout', views.spid_logout, name='spid_logout'),
    path(f'{SAML2_URL_PREFIX}metadata', views.metadata_spid, name='spid_metadata'),

    path(f'{SAML2_URL_PREFIX}acs', views.AssertionConsumerServiceView.as_view(), name='saml2_acs'),
    path(f'{SAML2_URL_PREFIX}ls', views.LogoutView.as_view(), name='saml2_ls'),
    path(f'{SAML2_URL_PREFIX}ls/post', views.LogoutView.as_view(), name='saml2_ls_post')
]

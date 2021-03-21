from django.urls import path

from django.conf import settings
from . import views


SPID_URLS_PREFIX = settings.SPID_URLS_PREFIX

urlpatterns = [
    path(f'{SPID_URLS_PREFIX}', views.index, name='index'),
    path(
            f'{SPID_URLS_PREFIX}/echo_attributes/',
            views.EchoAttributesView.as_view(),
            name='spid_echo_attributes'
    ),
    path(
            f'{SPID_URLS_PREFIX}/login/',
            views.spid_login,
            name='spid_login'
    ),
    path(
            f'{SPID_URLS_PREFIX}/logout/',
            views.spid_logout,
            name='spid_logout'
    ),
    path(
            settings.SPID_METADATA_URL_PATH,
            views.metadata_spid,
            name='spid_metadata'
    ),
    path(
            settings.SPID_ACS_URL_PATH,
            views.AssertionConsumerServiceView.as_view(),
            name='saml2_acs'
    ),
    path(
            settings.SPID_SLO_URL_PATH,
            views.LogoutView.as_view(),
            name='saml2_ls'
    ),
    path(
            settings.SPID_SLO_POST_URL_PATH,
            views.LogoutView.as_view(),
            name='saml2_ls_post'
    )
]

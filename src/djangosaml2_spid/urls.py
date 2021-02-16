from django.urls import include, path
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.views.generic.base import RedirectView


from djangosaml2 import views
from djangosaml2_spid.views import (metadata_spid,
                                    spid_login,
                                    spid_logout,
                                    index,
                                    EchoAttributesView)


SAML2_URL_PREFIX = 'spid'

urlpatterns = [
    # patched metadata for spid
    path(f'{SAML2_URL_PREFIX}/login/', spid_login, name='spid_login'),
    path(f'{SAML2_URL_PREFIX}/metadata/', metadata_spid, name='spid_metadata'),
    path(f'{SAML2_URL_PREFIX}/logout/', spid_logout, name='spid_logout'),
    
    path(f'{SAML2_URL_PREFIX}/acs/', views.AssertionConsumerServiceView.as_view(), name='saml2_acs'),
    path(f'{SAML2_URL_PREFIX}/ls/', views.LogoutView.as_view(), name='saml2_ls'),
    path(f'{SAML2_URL_PREFIX}/ls/post/', views.LogoutView.as_view(), name='saml2_ls_post'),
    path(f'{SAML2_URL_PREFIX}/echo_attributes', EchoAttributesView.as_view(), name='spid_echo_attributes'),
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),

    # path('', RedirectView.as_view(url='', permanent=False), name='index')
    path('', index, name='index')

    # path('spid/logout/', spid_logout,
         # {'next_page': settings.LOGOUT_REDIRECT_URL}, name='spid_logout'),
]

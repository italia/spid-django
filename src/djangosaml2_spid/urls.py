from django.urls import include, path
from django.conf import settings
from django.contrib import admin

from djangosaml2_spid.views import (metadata_spid,
                                    spid_login,
                                    spid_logout)

from . import views

urlpatterns = [
    # patched metadata for spid
    path('spid/metadata', metadata_spid, name='spid_metadata'),
    path('spid/login/', spid_login, name='spid_login'),

    # TODO
    path('spid/logout/', spid_logout,
         {'next_page': settings.LOGOUT_REDIRECT_URL},
         name='spid_logout'),
]

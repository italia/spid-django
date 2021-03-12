from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
]

if 'djangosaml2_spid' in settings.INSTALLED_APPS:
    import djangosaml2_spid.urls

    urlpatterns.extend([
        path('', include((djangosaml2_spid.urls, 'djangosaml2_spid',)))
    ])

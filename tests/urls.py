from django.contrib import admin
from django.urls import path, include
import djangosaml2_spid.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include((djangosaml2_spid.urls, 'djangosaml2_spid',))),
]

#
# Settings file for running the demo projects with Django's development server.
#
# noinspection PyUnresolvedReferences
from .settings import *

SESSION_COOKIE_SECURE = False  # Allows the sent of session cookie on http
CSRF_COOKIE_SECURE = False     # Allows the sent of csrf cookie on http
SPID_BASE_URL = None           # the base URL is got dynamically from request.build_absolute_uri('/')

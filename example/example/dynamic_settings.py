#
# Settings file for running the demo projects with dynamic base URL setting.
# Useful for running the demo with a non-local IP address.
#
# noinspection PyUnresolvedReferences
from .settings import *

SPID_BASE_URL = None  # With None the base URL is got dynamically from request.build_absolute_uri('/')

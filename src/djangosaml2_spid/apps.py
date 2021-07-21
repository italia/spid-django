from django.apps import AppConfig


class Djangosaml2SpidConfig(AppConfig):
    name = "djangosaml2_spid"

    def ready(self):
        try:
            from ._saml2 import pysaml2_patch, register_oasis_default_nsmap
            pysaml2_patch()
            register_oasis_default_nsmap()
        except ImportError:
            pass

from django import template
from django.conf import settings
from urllib.parse import urlparse

register = template.Library()


@register.simple_tag()
def spid_saml_check_url():
    url = urlparse(settings.SPID_SAML_CHECK_METADATA_URL)
    return f'{url.scheme}://{url.netloc}'


@register.simple_tag()
def spid_saml_check_demo_url():
    url = urlparse(settings.SPID_SAML_CHECK_DEMO_METADATA_URL)
    return f'{url.scheme}://{url.netloc}{url.path.rpartition("/")[0]}'

from django import template
from django.conf import settings
from urllib.parse import urlparse

register = template.Library()


@register.simple_tag()
def spid_saml_check_url():
    url = urlparse(settings.SPID_SAML_CHECK_METADATA_URL)
    return f'{url.scheme}://{url.netloc}'


@register.simple_tag()
def spid_testenv2_url():
    url = urlparse(settings.SPID_TESTENV2_METADATA_URL)
    return f'{url.scheme}://{url.netloc}'


@register.filter()
def spid_button_size(size):
    if size in {'short', 'medium', 'large', 'xlarge'}:
        return size
    elif size == 's':
        return 'small'
    elif size == 'm':
        return 'medium'
    elif size == 'xl':
        return 'xlarge'
    else:
        return 'large'

from django import template
from django.conf import settings
from urllib.parse import urlparse

register = template.Library()


@register.simple_tag()
def spid_saml_check_idp_active():
    return settings.SPID_SAML_CHECK_IDP_ACTIVE


@register.simple_tag()
def spid_saml_check_url():
    url = urlparse(settings.SPID_SAML_CHECK_METADATA_URL)
    return f"{url.scheme}://{url.netloc}"


@register.simple_tag()
def spid_demo_idp_active():
    return settings.SPID_DEMO_IDP_ACTIVE


@register.simple_tag()
def spid_demo_url():
    url = urlparse(settings.SPID_DEMO_METADATA_URL)
    return f'{url.scheme}://{url.netloc}{url.path.rpartition("/")[0]}'


@register.simple_tag()
def spid_validator_idp_active():
    return settings.SPID_VALIDATOR_IDP_ACTIVE


@register.simple_tag()
def spid_validator_url():
    url = urlparse(settings.SPID_VALIDATOR_METADATA_URL)
    return f"{url.scheme}://{url.netloc}"


@register.filter()
def spid_button_size(size):
    if size in {"short", "medium", "large", "xlarge"}:
        return size
    elif size == "s":
        return "small"
    elif size == "m":
        return "medium"
    elif size == "xl":
        return "xlarge"
    else:
        return "large"

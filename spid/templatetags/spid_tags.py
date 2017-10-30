import random

from django import template
from django.conf import settings
from ..apps import SpidConfig

register = template.Library()

SPID_BUTTON_SIZES = {'small', 'medium', 'large', 'xlarge'}


@register.inclusion_tag("spid_button.html", takes_context=True)
def spid_button(context, size='medium'):
    if size not in SPID_BUTTON_SIZES:
        raise ValueError("argument 'size': value %r not in %r." % (size, SPID_BUTTON_SIZES))

    spid_idp_list = [
        {'id': k, 'name': v['name']}
        for k, v in SpidConfig.identity_providers.items()
    ]
    random.shuffle(spid_idp_list)
    if settings.DEBUG:
        spid_idp_list.append({'id': 'test', 'name': 'test'})
    return {
        'method': context['request'].method.lower(),
        'post_data': context['request'].POST,
        'spid_button_size': size,
        'spid_button_size_short': size[0] if size != 'xlarge' else size[:2],
        'spid_idp_list': spid_idp_list
    }

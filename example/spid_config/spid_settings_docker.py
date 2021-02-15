from django.conf import settings
import os

is_dockerized_example = os.environ.get('SPID_DJANGO_DOCKERIZED_EXAMPLE') != ''

if is_dockerized_example:
    SPID_DEFAULT_BINDING = settings.SPID_DEFAULT_BINDING
    SAML_CONFIG = settings.SAML_CONFIG

    BASE = 'http://hostnet:8000'
    BASE_URL = '{}/spid'.format(BASE)

    SAML_CONFIG.update({
        'entityid': f'{BASE_URL}/metadata',
        'metadata': {
            "remote": [
                {"url": "http://hostnet:8080/metadata.xml"},
                {'url': 'http://hostnet:8088/metadata'},
            ]
        }
    })

    SAML_CONFIG['service']['sp'].update({
        'name': f'{BASE_URL}/metadata',
        'name_qualifier': BASE,
        'endpoints': {
            'assertion_consumer_service': [
                (f'{BASE_URL}/acs/', SPID_DEFAULT_BINDING),
            ],
            "single_logout_service": [
                (f'{BASE_URL}/ls/post/', SPID_DEFAULT_BINDING),
            ],
        }
    })

print(SAML_CONFIG)

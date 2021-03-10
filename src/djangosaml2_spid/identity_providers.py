# source: https://registry.spid.gov.it/identity-providers

import urllib.request
import json

identity_providers_url = 'https://registry.spid.gov.it/assets/data/idp.json'


def download_identity_providers():
    with urllib.request.urlopen(identity_providers_url) as response:
        identity_providers = json.loads(response.read())['data']

    for identity_provider in identity_providers:
        with urllib.request.urlopen(identity_provider["metadata_url"]) as response:
            identity_provider['metadata'] = str(response.read())

    return identity_providers

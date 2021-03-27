from .spid_settings import *
from typing import Dict, List
import os
# new features parameter
SPID_CURRENT_INDEX: int = int(os.getenv("SPID_CURRENT_INDEX", "0"), 10)  # in my case export SPID_CURRENT_INDEX=1

SAML_ATTRIBUTE_CONSUMING_SERVICE_LIST = [
    {
        "serviceNames": (
            {"lang": "en", "text": "service #1"},
            {"lang": "it", "text": "servizio #1"},
        ),
        "serviceDescriptions": (
            {"lang": "en", "text": "description of service #1"},
            {"lang": "it", "text": "descrizione del servizio #1"},
        ),
        "attributes": ("spidCode", "fiscalNumber", "email", "name", "familyName", "placeOfBirth", "dateOfBirth",)
    }
]

sp: Dict = SAML_CONFIG.get("service", {}).get("sp", {})
endpoints: List = sp.get("endpoints", [])

assertion_consumer_service: List = endpoints.get("assertion_consumer_service")

single_logout_service: List = endpoints.get("single_logout_service", [])

encryption_keypairs = List = SAML_CONFIG.get("encryption_keypairs", [])

if 1 == SPID_CURRENT_INDEX:
    assertion_consumer_service.insert(0, (f'https://previousservice.example.it/acs', SPID_DEFAULT_BINDING))

    single_logout_service.insert(0, (f'https://previousservice.example.it/ls/post', SPID_DEFAULT_BINDING))

    encryption_keypairs.insert(0,
                               {
                                   # use private key of current production service (index="0")
                                   'key_file': SPID_PRIVATE_KEY,
                                   # use public crt of current production service (index="0")
                                   'cert_file': SPID_PUBLIC_CERT,

                               })

    SAML_ATTRIBUTE_CONSUMING_SERVICE_LIST.append(
        {
            "serviceNames": (
                {"lang": "en", "text": "service #2"},
                {"lang": "it", "text": "servizio #2"},
            ),
            "serviceDescriptions": (
                {"lang": "en", "text": "description of service #2"},
                {"lang": "it", "text": "descrizione del servizio #2"},
            ),
            "attributes": ("spidCode", "fiscalNumber", "email", "name", "familyName",)
        }
    )

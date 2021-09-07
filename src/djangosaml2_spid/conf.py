import os
import copy
import logging
from urllib.parse import urljoin
from typing import Optional

import saml2
from saml2.config import SPConfig
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.sigver import get_xmlsec_binary
from saml2.xmldsig import DIGEST_SHA256, SIG_RSA_SHA256

from django.conf import settings
from django.apps import apps
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

logger = logging.getLogger("djangosaml2")

djangosaml2_spid_config = apps.get_app_config("djangosaml2_spid")


#
# Required settings

if not hasattr(settings, "SPID_CONTACTS"):
    raise ImproperlyConfigured("Manca la configurazione SPID_CONTACTS!")

if not hasattr(settings, "SAML_CONFIG"):
    raise ImproperlyConfigured(
        "Manca la configurazione base per SAML2 "
        "con le informazioni sull'organizzazione!"
    )
elif not isinstance(settings.SAML_CONFIG, dict):
    raise ImproperlyConfigured("Formato improprio per la configurazione SAML2!")
elif "organization" not in settings.SAML_CONFIG:
    raise ImproperlyConfigured(
        "Mancano le informazioni sull'organizzazione nella configurazione SAML2!"
    )

#
# SPID settings with default values

settings.SPID_BASE_URL = getattr(settings, "SPID_BASE_URL", None)
settings.SPID_URLS_PREFIX = getattr(settings, "SPID_URLS_PREFIX", "spid")
settings.CIE_URLS_PREFIX = getattr(settings, "CIE_URLS_PREFIX", "cie")

settings.SPID_ACS_URL_PATH = getattr(
    settings, "SPID_ACS_URL_PATH", f"{settings.SPID_URLS_PREFIX}/acs/"
)
settings.SPID_SLO_POST_URL_PATH = getattr(
    settings, "SPID_SLO_POST_URL_PATH", f"{settings.SPID_URLS_PREFIX}/ls/post/"
)
settings.SPID_SLO_URL_PATH = getattr(
    settings, "SPID_SLO_URL_PATH", f"{settings.SPID_URLS_PREFIX}/ls/"
)
settings.SPID_METADATA_URL_PATH = getattr(
    settings, "SPID_METADATA_URL_PATH", f"{settings.SPID_URLS_PREFIX}/metadata/"
)
settings.CIE_METADATA_URL_PATH = getattr(
    settings, "CIE_METADATA_URL_PATH", f"{settings.CIE_URLS_PREFIX}/metadata/"
)

settings.LOGIN_URL = getattr(settings, "LOGIN_URL", "/spid/login")
settings.LOGOUT_URL = getattr(settings, "LOGOUT_URL", "/spid/logout")
settings.LOGIN_REDIRECT_URL = getattr(
    settings, "LOGIN_REDIRECT_URL", "/spid/echo_attributes"
)

settings.SAML2_DEFAULT_BINDING = getattr(
    settings, "SAML2_DEFAULT_BINDING", saml2.BINDING_HTTP_POST
)

settings.SPID_DIG_ALG = getattr(settings, "SPID_DIG_ALG", DIGEST_SHA256)
settings.SPID_SIG_ALG = getattr(settings, "SPID_SIG_ALG", SIG_RSA_SHA256)

settings.SPID_NAMEID_FORMAT = getattr(
    settings, "SPID_NAMEID_FORMAT", NAMEID_FORMAT_TRANSIENT
)

SPID_ACR_L1 = "https://www.spid.gov.it/SpidL1"
SPID_ACR_L2 = "https://www.spid.gov.it/SpidL2"
SPID_ACR_L3 = "https://www.spid.gov.it/SpidL3"

settings.SPID_AUTH_CONTEXT = getattr(settings, "SPID_AUTH_CONTEXT", SPID_ACR_L1)

settings.SPID_ACR_FAUTHN_MAP = getattr(
    settings,
    "SPID_ACR_FAUTHN_MAP",
    {SPID_ACR_L1: "false", SPID_ACR_L2: "true", SPID_ACR_L3: "true"},
)

settings.SPID_CERTS_DIR = getattr(
    settings, "SPID_CERTS_DIR", os.path.join(settings.BASE_DIR, "certificates/")
)
settings.SPID_PUBLIC_CERT = getattr(
    settings, "SPID_PUBLIC_CERT", os.path.join(settings.SPID_CERTS_DIR, "public.cert")
)
settings.SPID_PRIVATE_KEY = getattr(
    settings, "SPID_PRIVATE_KEY", os.path.join(settings.SPID_CERTS_DIR, "private.key")
)

# source: https://registry.spid.gov.it/identity-providers
settings.SPID_IDENTITY_PROVIDERS_URL = getattr(
    settings,
    "SPID_IDENTITY_PROVIDERS_URL",
    "https://registry.spid.gov.it/assets/data/idp.json",
)

settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR = getattr(
    settings,
    "SPID_IDENTITY_PROVIDERS_METADATA_DIR",
    getattr(
        settings,
        "SPID_IDENTITY_PROVIDERS_METADATAS_DIR",
        os.path.join(settings.BASE_DIR, "metadata/"),
    ),
)

# Validation tools settings
if hasattr(settings, "SPID_SAML_CHECK_IDP_ACTIVE"):
    pass
elif "SPID_SAML_CHECK_IDP_ACTIVE" in os.environ:
    settings.SPID_SAML_CHECK_IDP_ACTIVE = (
        os.environ["SPID_SAML_CHECK_IDP_ACTIVE"] == "True"
    )
else:
    # Checks the old setting name
    settings.SPID_SAML_CHECK_IDP_ACTIVE = getattr(
        settings,
        "SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE",
        os.environ.get("SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE", "False") == "True",
    )

settings.SPID_SAML_CHECK_METADATA_URL = getattr(
    settings,
    "SPID_SAML_CHECK_METADATA_URL",
    os.environ.get(
        "SPID_SAML_CHECK_METADATA_URL", "https://localhost:8080/metadata.xml"
    ),
)

settings.SPID_DEMO_IDP_ACTIVE = getattr(
    settings, "SPID_DEMO_IDP_ACTIVE", os.environ.get("SPID_DEMO_IDP_ACTIVE", "False") == "True"
)

settings.SPID_DEMO_METADATA_URL = getattr(
    settings,
    "SPID_DEMO_METADATA_URL",
    os.environ.get("SPID_DEMO_METADATA_URL", "https://demo.spid.gov.it/metadata.xml"),
)

settings.SPID_VALIDATOR_IDP_ACTIVE = getattr(
    settings, "SPID_VALIDATOR_IDP_ACTIVE", False
)

settings.SPID_VALIDATOR_METADATA_URL = getattr(
    settings,
    "SPID_VALIDATOR_METADATA_URL",
    "https://validator.spid.gov.it/metadata.xml",
)

# Avviso 29v3
settings.SPID_PREFIXES = getattr(
    settings,
    "SPID_PREFIXES",
    dict(
        spid="https://spid.gov.it/saml-extensions",
        fpa="https://spid.gov.it/invoicing-extensions",
    ),
)

settings.CIE_PREFIXES = getattr(
    settings,
    "CIE_PREFIXES",
    dict(
        cie="https://www.cartaidentita.interno.gov.it/saml-extensions"
    ),
)

#
# Defaults for other SAML settings

settings.SAML_CONFIG_LOADER = getattr(
    settings, "SAML_CONFIG_LOADER", "djangosaml2_spid.conf.config_settings_loader"
)

# OR NAME_ID or MAIN_ATTRIBUTE (not together!)
settings.SAML_USE_NAME_ID_AS_USERNAME = getattr(
    settings, "SAML_USE_NAME_ID_AS_USERNAME", False
)
settings.SAML_DJANGO_USER_MAIN_ATTRIBUTE = getattr(
    settings, "SAML_DJANGO_USER_MAIN_ATTRIBUTE", "username"
)
settings.SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP = getattr(
    settings, "SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP", "__iexact"
)
settings.SAML_CREATE_UNKNOWN_USER = getattr(settings, "SAML_CREATE_UNKNOWN_USER", True)

# logout
settings.SAML_LOGOUT_REQUEST_PREFERRED_BINDING = getattr(
    settings, "SAML_LOGOUT_REQUEST_PREFERRED_BINDING", saml2.BINDING_HTTP_POST
)

settings.SAML_ATTRIBUTE_MAPPING = getattr(
    settings,
    "SAML_ATTRIBUTE_MAPPING",
    {
        "spidCode": ("username",),
        "fiscalNumber": ("tin",),
        "email": ("email",),
        "name": ("first_name",),
        "familyName": ("last_name",),
        "placeOfBirth": ("place_of_birth",),
        "dateOfBirth": ("birth_date",),
    },
)

settings.SPID_ATTR_MAP_DIR = getattr(
    settings,
    "SPID_ATTR_MAP_DIR",
    os.path.join(
            djangosaml2_spid_config.path, "attribute_maps/"
        )
)

# Attributes that this project need to identify a user
settings.SPID_REQUIRED_ATTRIBUTES = getattr(
    settings,
    "SPID_REQUIRED_ATTRIBUTES",
    [
        "spidCode",
        "name",
        "familyName",
        "fiscalNumber",
        "email",
    ],
)

settings.CIE_REQUIRED_ATTRIBUTES = getattr(
    settings,
    "CIE_REQUIRED_ATTRIBUTES",
    [
        "name",
        "familyName",
        "fiscalNumber",
        "dateOfBirth",
    ],
)


# Attributes that may be useful to have but not required
settings.SPID_OPTIONAL_ATTRIBUTES = getattr(
    settings,
    "SPID_OPTIONAL_ATTRIBUTES",
    [
        "gender",
        "companyName",
        "registeredOffice",
        "ivaCode",
        "idCard",
        "digitalAddress",
        "placeOfBirth",
        "countyOfBirth",
        "dateOfBirth",
        "address",
        "mobilePhone",
        "expirationDate",
    ],
)


def config_settings_loader(request: Optional[HttpRequest] = None) -> SPConfig:
    conf = SPConfig()
    if request is None:
        # Not a SPID request: load SAML_CONFIG unchanged
        conf.load(copy.deepcopy(settings.SAML_CONFIG))
        return conf

    # Build a SAML_CONFIG for SPID
    base_url = settings.SPID_BASE_URL or request.build_absolute_uri("/")
    metadata_url = urljoin(base_url, settings.SPID_METADATA_URL_PATH)

    if settings.SPID_METADATA_URL_PATH in request.get_full_path():
        _REQUIRED_ATTRIBUTES = settings.SPID_REQUIRED_ATTRIBUTES
        _OPTIONAL_ATTRIBUTES = settings.SPID_OPTIONAL_ATTRIBUTES
    else:
        _REQUIRED_ATTRIBUTES = settings.CIE_REQUIRED_ATTRIBUTES
        _OPTIONAL_ATTRIBUTES = []

    saml_config = {
        "entityid": getattr(settings, 'SAML2_ENTITY_ID', metadata_url),
        "attribute_map_dir": settings.SPID_ATTR_MAP_DIR,
        "service": {
            "sp": {
                "name": metadata_url,
                "name_qualifier": base_url,
                "name_id_format": [settings.SPID_NAMEID_FORMAT],
                "endpoints": {
                    "assertion_consumer_service": [
                        (
                            urljoin(base_url, reverse("djangosaml2_spid:saml2_acs")),
                            saml2.BINDING_HTTP_POST,
                        ),
                    ],
                    "single_logout_service": [
                        (
                            urljoin(
                                base_url, reverse("djangosaml2_spid:saml2_ls_post")
                            ),
                            saml2.BINDING_HTTP_POST,
                        ),
                    ],
                },
                # Mandates that the IdP MUST authenticate the presenter directly
                # rather than rely on a previous security context.
                "force_authn": False,  # SPID
                "name_id_format_allow_create": False,
                # attributes that this project need to identify a user

                "required_attributes": _REQUIRED_ATTRIBUTES,
                "optional_attributes": _OPTIONAL_ATTRIBUTES,

                "requested_attribute_name_format": saml2.saml.NAME_FORMAT_BASIC,
                "name_format": saml2.saml.NAME_FORMAT_BASIC,
                "signing_algorithm": settings.SPID_SIG_ALG,
                "digest_algorithm": settings.SPID_DIG_ALG,
                "authn_requests_signed": True,
                "logout_requests_signed": True,
                # Indicates that Authentication Responses to this SP must
                # be signed. If set to True, the SP will not consume
                # any SAML Responses that are not signed.
                "want_assertions_signed": True,
                # When set to true, the SP will consume unsolicited SAML
                # Responses, i.e. SAML Responses for which it has not sent
                # a respective SAML Authentication Request. Set to True to
                # let ACS endpoint work.
                "allow_unsolicited": settings.SAML_CONFIG.get(
                    "allow_unsolicited", False
                ),
                # Permits to have attributes not configured in attribute-mappings
                # otherwise...without OID will be rejected
                "allow_unknown_attributes": True,
            },
        },
        "disable_ssl_certificate_validation": settings.SAML_CONFIG.get(
            "disable_ssl_certificate_validation"
        ),
        "metadata": {
            "local": [settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR],
            "remote": [],
        },
        # Signing
        "key_file": settings.SPID_PRIVATE_KEY,
        "cert_file": settings.SPID_PUBLIC_CERT,
        # Encryption
        "encryption_keypairs": [
            {
                "key_file": settings.SPID_PRIVATE_KEY,
                "cert_file": settings.SPID_PUBLIC_CERT,
            }
        ],
        "organization": copy.deepcopy(settings.SAML_CONFIG["organization"]),
    }

    if settings.SAML_CONFIG.get("debug"):
        saml_config["debug"] = True

    if "xmlsec_binary" in settings.SAML_CONFIG:
        saml_config["xmlsec_binary"] = copy.deepcopy(
            settings.SAML_CONFIG["xmlsec_binary"]
        )
    else:
        saml_config["xmlsec_binary"] = get_xmlsec_binary(
            ["/opt/local/bin", "/usr/bin/xmlsec1"]
        )

    if settings.SPID_SAML_CHECK_IDP_ACTIVE:
        saml_config["metadata"]["remote"].append(
            {"url": settings.SPID_SAML_CHECK_METADATA_URL}
        )

    if settings.SPID_DEMO_IDP_ACTIVE:
        saml_config["metadata"]["remote"].append(
            {"url": settings.SPID_DEMO_METADATA_URL}
        )

    if settings.SPID_VALIDATOR_IDP_ACTIVE:
        saml_config["metadata"]["remote"].append(
            {"url": settings.SPID_VALIDATOR_METADATA_URL}
        )

    logger.debug(f"SAML_CONFIG: {saml_config}")
    conf.load(saml_config)
    return conf

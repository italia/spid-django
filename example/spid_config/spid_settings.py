from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.sigver import get_xmlsec_binary
import os
import saml2

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPID_BASE_SCHEMA_HOST_PORT = os.environ.get('SPID_BASE_SCHEMA_HOST_PORT', 'http://localhost:8000')
SPID_URLS_PREFIX = 'spid/'
SPID_BASE_URL = f'{SPID_BASE_SCHEMA_HOST_PORT}/{SPID_URLS_PREFIX}'

LOGIN_URL = '/spid/login'
LOGOUT_URL = '/spid/logout'
LOGIN_REDIRECT_URL = '/spid/echo_attributes'
LOGOUT_REDIRECT_URL = '/'

SPID_DEFAULT_BINDING = saml2.BINDING_HTTP_POST
SPID_DIG_ALG = saml2.xmldsig.DIGEST_SHA256
SPID_SIG_ALG = saml2.xmldsig.SIG_RSA_SHA256
SPID_NAMEID_FORMAT = NAMEID_FORMAT_TRANSIENT
SPID_AUTH_CONTEXT = 'https://www.spid.gov.it/SpidL1'

SPID_CERTS_DIR = os.path.join(os.environ.get('PWD'), 'certificates/')
SPID_PUBLIC_CERT = os.path.join(SPID_CERTS_DIR, 'public.cert')
SPID_PRIVATE_KEY = os.path.join(SPID_CERTS_DIR, 'private.key')

# source: https://registry.spid.gov.it/identity-providers
SPID_IDENTITY_PROVIDERS_URL = 'https://registry.spid.gov.it/assets/data/idp.json'
SPID_IDENTITY_PROVIDERS_METADATAS_DIR = os.path.join(BASE_DIR, 'spid_config/metadata/')

SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE = os.environ.get('SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE', 'False') == 'True'
SPID_SAML_CHECK_METADATA_URL = os.environ.get('SPID_SAML_CHECK_METADATA_URL', 'http://localhost:8080/metadata.xml')

SPID_TESTENV2_REMOTE_METADATA_ACTIVE = os.environ.get('SPID_TESTENV2_REMOTE_METADATA_ACTIVE', 'False') == 'True'
SPID_TESTENV2_METADATA_URL = os.environ.get('SPID_TESTENV2_METADATA_URL', 'http://localhost:8088/metadata')

# Avviso 29v3
SPID_PREFIXES = dict(
    spid='https://spid.gov.it/saml-extensions',
    fpa='https://spid.gov.it/invoicing-extensions'
)

SPID_CONTACTS = [
    {
        'contact_type': 'other',
        'telephone_number': '+39 8475634785',
        'email_address': 'tech-info@example.org',
        'VATNumber': 'IT12345678901',
        'FiscalCode': 'XYZABCAAMGGJ000W',
        'Private': ''
    },
    {
        'contact_type': 'billing',
        'telephone_number': '+39 84756344785',
        'email_address': 'info@example.org',
        'company': 'example s.p.a.',
        # 'CodiceFiscale': 'NGLMRA80A01D086T',
        'IdCodice': '983745349857',
        'IdPaese': 'IT',
        'Denominazione': 'Destinatario Fatturazione',
        'Indirizzo': 'via tante cose',
        'NumeroCivico': '12',
        'CAP': '87100',
        'Comune': 'Cosenza',
        'Provincia': 'CS',
        'Nazione': 'IT',
    },
]

SAML_CONFIG = {
    'debug': True,
    'xmlsec_binary': get_xmlsec_binary(['/opt/local/bin', '/usr/bin/xmlsec1']),
    'entityid': f'{SPID_BASE_URL}metadata',
    'attribute_map_dir': f'{BASE_DIR}/spid_config/attribute-maps/',

    'service': {
        'sp': {
            'name': f'{SPID_BASE_URL}metadata',
            'name_qualifier': SPID_BASE_SCHEMA_HOST_PORT,

            'name_id_format': [SPID_NAMEID_FORMAT],

            'endpoints': {
                'assertion_consumer_service': [
                    (f'{SPID_BASE_URL}acs', SPID_DEFAULT_BINDING),
                ],
                'single_logout_service': [
                    (f'{SPID_BASE_URL}ls/post', SPID_DEFAULT_BINDING),
                    # (f'{SPID_BASE_URL}/ls', saml2.BINDING_HTTP_REDIRECT),
                ],
            },

            # Mandates that the IdP MUST authenticate the presenter directly
            # rather than rely on a previous security context.
            'force_authn': False,  # SPID
            'name_id_format_allow_create': False,

            # attributes that this project need to identify a user
            'required_attributes': [
                'spidCode',
                'name',
                'familyName',
                'fiscalNumber',
                'email'
            ],

            'requested_attribute_name_format': saml2.saml.NAME_FORMAT_BASIC,
            'name_format': saml2.saml.NAME_FORMAT_BASIC,

            # attributes that may be useful to have but not required
            'optional_attributes': [
                'gender',
                'companyName',
                'registeredOffice',
                'ivaCode',
                'idCard',
                'digitalAddress',
                'placeOfBirth',
                'countyOfBirth',
                'dateOfBirth',
                'address',
                'mobilePhone',
                'expirationDate'
            ],

            'signing_algorithm': SPID_SIG_ALG,
            'digest_algorithm': SPID_DIG_ALG,

            'authn_requests_signed': True,
            'logout_requests_signed': True,

            # Indicates that Authentication Responses to this SP must
            # be signed. If set to True, the SP will not consume
            # any SAML Responses that are not signed.
            'want_assertions_signed': True,

            # When set to true, the SP will consume unsolicited SAML
            # Responses, i.e. SAML Responses for which it has not sent
            # a respective SAML Authentication Request.
            'allow_unsolicited': False,

            # Permits to have attributes not configured in attribute-mappings
            # otherwise...without OID will be rejected
            'allow_unknown_attributes': True,
        },
    },

    # many metadata, many idp...
    'metadata': {
        'local': [
            SPID_IDENTITY_PROVIDERS_METADATAS_DIR
        ],
        'remote': []
    },

    # Signing
    'key_file': SPID_PRIVATE_KEY,
    'cert_file': SPID_PUBLIC_CERT,

    # Encryption
    'encryption_keypairs': [{
        'key_file': SPID_PRIVATE_KEY,
        'cert_file': SPID_PUBLIC_CERT,
    }],

    # you can set multilanguage information here
    'organization': {
        'name': [('Example', 'it'), ('Example', 'en')],
        'display_name': [('Example', 'it'), ('Example', 'en')],
        'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')],
    },
}

if SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE:
    SAML_CONFIG['metadata']['remote'].append(
        {'url': SPID_SAML_CHECK_METADATA_URL}
    )

if SPID_TESTENV2_REMOTE_METADATA_ACTIVE:
    SAML_CONFIG['metadata']['remote'].append(
        {'url': SPID_TESTENV2_METADATA_URL}
    )

# OR NAME_ID or MAIN_ATTRIBUTE (not together!)
SAML_USE_NAME_ID_AS_USERNAME = False

SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'username'
SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP = '__iexact'

SAML_CREATE_UNKNOWN_USER = True

# logout
SAML_LOGOUT_REQUEST_PREFERRED_BINDING = saml2.BINDING_HTTP_POST

SAML_ATTRIBUTE_MAPPING = {
    'spidCode': ('username', ),
    'fiscalNumber': ('tin', ),
    'email': ('email', ),
    'name': ('first_name', ),
    'familyName': ('last_name', ),
    'placeOfBirth': ('place_of_birth',),
    'dateOfBirth': ('birth_date',),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'default': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(message)s [(%(levelname)s)] %(args)s %(name)s %(filename)s.%(funcName)s:%(lineno)s]'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "msg": %(message)s, "level": "%(levelname)s",  "name": "%(name)s", "path": "%(filename)s.%(funcName)s:%(lineno)s", "@source":"django-audit"}'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'formatter': 'detailed',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'djangosaml2_spid.tests': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

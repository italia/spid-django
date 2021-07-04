from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.sigver import get_xmlsec_binary
import os
import saml2

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPID_BASE_URL = "https://localhost:8000"
SPID_URLS_PREFIX = 'spid'

SPID_ACS_URL_PATH = f'{SPID_URLS_PREFIX}/acs/'
SPID_SLO_POST_URL_PATH = f'{SPID_URLS_PREFIX}/ls/post/'
SPID_SLO_URL_PATH = f'{SPID_URLS_PREFIX}/ls/'
SPID_METADATA_URL_PATH = f'{SPID_URLS_PREFIX}/metadata/'

LOGIN_URL = f'/{SPID_URLS_PREFIX}/login'
LOGOUT_URL = f'/{SPID_URLS_PREFIX}/logout'
LOGIN_REDIRECT_URL = f'/{SPID_URLS_PREFIX}/echo_attributes'
LOGOUT_REDIRECT_URL = '/'

SAML2_DEFAULT_BINDING = saml2.BINDING_HTTP_POST
SPID_DIG_ALG = saml2.xmldsig.DIGEST_SHA256
SPID_SIG_ALG = saml2.xmldsig.SIG_RSA_SHA256
SPID_NAMEID_FORMAT = NAMEID_FORMAT_TRANSIENT
SPID_AUTH_CONTEXT = 'https://www.spid.gov.it/SpidL1'

SPID_CERTS_DIR = os.path.join(os.environ.get('PWD'), 'certificates/')
SPID_PUBLIC_CERT = os.path.join(SPID_CERTS_DIR, 'public.cert')
SPID_PRIVATE_KEY = os.path.join(SPID_CERTS_DIR, 'private.key')

# source: https://registry.spid.gov.it/identity-providers
SPID_IDENTITY_PROVIDERS_URL = 'https://registry.spid.gov.it/assets/data/idp.json'
SPID_IDENTITY_PROVIDERS_METADATA_DIR = os.path.join(BASE_DIR, 'spid_config/metadata/')

SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE = os.environ.get('SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE', 'False') == 'True'
SPID_SAML_CHECK_METADATA_URL = os.environ.get('SPID_SAML_CHECK_METADATA_URL', 'http://localhost:8080/metadata.xml')

SPID_SAML_CHECK_DEMO_REMOTE_METADATA_ACTIVE = os.environ.get('SPID_SAML_CHECK_DEMO_REMOTE_METADATA_ACTIVE', 'False') == 'True'
SPID_SAML_CHECK_DEMO_METADATA_URL = os.environ.get('SPID_SAML_CHECK_DEMO_METADATA_URL', 'http://localhost:8080/demo/metadata.xml')

# Avviso 29v3
SPID_PREFIXES = dict(
    spid='https://spid.gov.it/saml-extensions',
    fpa='https://spid.gov.it/invoicing-extensions'
)

# Avviso SPID n. 19 v.4 per enti AGGREGATORI aggiungere chiave vuota PublicServicesFullOperator
# Il plugin genererà automaticamente anche il tag ContactPerson con l’attributo spid:entityType valorizzato a spid:aggregator

SPID_CONTACTS = [
    {
        'contact_type': 'other',
        'telephone_number': '+398475634785',
        'email_address': 'tech-info@example.org',
        'IPACode': 'that-IPA-code',
        'VATNumber': 'IT12345678901',
        'FiscalCode': 'XYZABCAAMGGJ000W',
        'Public': '',
        #'PublicServicesFullOperator':''
    },
    # {
        # 'contact_type': 'billing',
        # 'telephone_number': '+39 84756344785',
        # 'email_address': 'info@example.org',
        # 'company': 'example s.p.a.',
        ## 'CodiceFiscale': 'NGLMRA80A01D086T',
        # 'IdCodice': '983745349857',
        # 'IdPaese': 'IT',
        # 'Denominazione': 'Destinatario Fatturazione',
        # 'Indirizzo': 'via tante cose',
        # 'NumeroCivico': '12',
        # 'CAP': '87100',
        # 'Comune': 'Cosenza',
        # 'Provincia': 'CS',
        # 'Nazione': 'IT',
    # },
]


# Configuration for pysaml2 as managed by djangosaml2. For SPID SP service the most
# part is built dynamically from provided SPID_* settings and from SPID_* defaults.
SAML_CONFIG = {
    # Required organization info, you can set multi-language information here.
    'organization': {
        'name': [('Example', 'it'), ('Example', 'en')],
        'display_name': [('Example', 'it'), ('Example', 'en')],
        'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')],
    },

    # Other common options used by SPID configuration
    'debug': True,
    'xmlsec_binary': get_xmlsec_binary(['/opt/local/bin', '/usr/bin/xmlsec1']),

    # The other entries are dynamically generated from SPID_* provided settings
    # and defaults. You can still provide those entries here but they can useful
    # only for other SAML2 service in your installation, not for SPID.
    #
    # If you want to provide a full static SAML_CONFIG you need to define also
    # SAML_CONFIG_LOADER setting, typically it can be set pointing to the default
    # djangosaml2's config loader function:
    #
    #   SAML_CONFIG_LOADER = 'djangosaml2.conf.config_settings_loader'
    #
}

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

"""
djangosaml2_spid settings for running tests.
"""
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-%1f#b#w9t%g%job)vd&f7pxdl!_zu%!mxx197bixh8&%*(%nb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'djangosaml2',
    'djangosaml2_spid',
    'tests',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # SAML session with SameSite = None
    'djangosaml2.middleware.SamlSessionMiddleware'
]

if 'djangosaml2' in INSTALLED_APPS or \
   'djangosaml2_spid' in INSTALLED_APPS:

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'djangosaml2.backends.Saml2Backend',
    )

# AUTH_USER_MODEL = 'tests.custom_accounts.User'
ROOT_URLCONF = 'tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'tests.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'


# PySAML2 base settings
SAML_CONFIG = {
    'organization': {
        'name': [('Example', 'it'), ('Example', 'en')],
        'display_name': [('Example', 'it'), ('Example', 'en')],
        'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')],
    },
}


# SPID required settings
SPID_CERTS_DIR = 'tests/certificates/'
SPID_IDENTITY_PROVIDERS_METADATA_DIR = 'tests/metadata/'

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

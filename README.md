SPID/CIE Django
-----------

![CI build](https://github.com/italia/spid-django/workflows/spid-django/badge.svg)
![Python version](https://img.shields.io/badge/license-Apache%202-blue.svg)
![License](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue.svg)


A SPID/CIE Service Provider based on [pysaml2](https://github.com/identitypython/pysaml2).


Introduction
------------

This is a Django application that provides a SAML2 Service Provider
for a Single Sign On with SPID and CIE, the Italian Digital Identity System.

This project comes with a demo on a Spid button template with *spid-saml-check* IDP preconfigured.
See running the Demo project paragaph for details.

Furthermore, this application integrates the checks of
[Spid QA](https://www.spid.gov.it/assets/download/SPID_QAD.pdf)
within its CI pipeline, through [spid-sp-test](https://github.com/peppelinux/spid-sp-test).
See github actions log for details.

The technical documentation on SPID and SAML is available at [Docs Italia](https://docs.italia.it/italia/spid/spid-regole-tecniche)
The technical documentation on CIE and SAML is available at [Docs Italia](https://docs.italia.it/italia/cie/cie-manuale-tecnico-docs)


![big picture](gallery/animated.gif)


Dependencies
------------

These libraries are required on your operating system environment
in order to compile external modules of some dependencies:

- xmlsec
- python3-dev
- python3-pip
- libssl-dev
- libsasl2-dev


Running the Demo project
------------------------

The demo project is configured within `example/` subdirectory.
This project uses **spid-saml-check** as demo IDP.

Prepare environment:
````
cd example/
virtualenv -ppython3 env
source env/bin/activate

pip install djangosaml2-spid
````

⚠️ djangosaml2-spid uses a *monkey-patch* version of the pysaml2 library that fixes 
some limitations or small bugs that can affect SPID data. Patches are applied only 
once after the app is ready to run. Take a look at module `djangosaml2_spid._saml2` 
for patches code and references.


Your example saml2 configuration is in `spid_config/spid_settings.py`.
See djangosaml2 and pysaml2 official docs for clarifications.

To run the demo project:
 - python -B ./manage.py migrate
 - python -B ./manage.py collectstatic --noinput
 - uwsgi --https 0.0.0.0:8000,./certificates/public.cert,./certificates/private.key --module example.wsgi:application --env example.settings --chdir .

or execute the run.sh script with these environment settings to enable tests IdPs:

````
SPID_SAML_CHECK_IDP_ACTIVE=True SPID_DEMO_IDP_ACTIVE=True bash run.sh
````

If you chose to use your own demo IdP you just have to save the
current demo metadata in the demo IdP configuration, this way:

````
# cd into demo IdP metadata folder ...
wget https://localhost:8000/spid/metadata -O conf/sp_metadata.xml
````

Finally, start pid-saml-check (docker is suggested) and open 'https://localhost:8000' in your browser.


Demo project with Docker
------------------------

To use Docker compose environment, add to /etc/hosts this line:
````
127.0.0.1   hostnet
````

then use `docker-compose --env-file docker-compose.env up` (the process takes some time) and when the services are up go to http://hostnet:8000/spid/login

**warning**: if you want to change ports of any of the docker-compose services (as, spid-saml-check) and/or the FQDN of the docker-compose default network gateway (defaults to `hostnet`) you need to change all the files
under `./example/configs/` to match the new configurations, changing only `./docker-compose.env` will not suffice.


Setup for an existing project
-----------------------------

djangosaml2_spid uses a pySAML2 fork.

* `pip install git+https://github.com/italia/spid-django`
* Copy the `example/spid_config/` to your project base dir and remember to edit with your custom paramenters
* Import SAML2 entity configuration in your project settings file: `from spid_config.spid_settings import *`
* Add in `settings.INSTALLED_APPS` the following
  ```
    'djangosaml2',
    'djangosaml2_spid',
    'spid_config'
  ```
  _spid_config_ is your configuration, with statics and templates. See `example` project.
* Add you custom User model, see example project: `AUTH_USER_MODEL = 'custom_accounts.User'`
* Add in `settings.MIDDLEWARE`: `'djangosaml2.middleware.SamlSessionMiddleware'` for [SameSite Cookie](https://github.com/knaperek/djangosaml2#samesite-cookie)
* Add in `settings.AUTHENTICATION_BACKENDS`:
  ```
    'django.contrib.auth.backends.ModelBackend',
    'djangosaml2.backends.Saml2Backend',
  ```
* Generate X.509 certificates and store them to a path, generally in `./certificates`, using [spid-compliant-certificates](https://github.com/italia/spid-compliant-certificates)
* Register the SP metadata to your test Spid IDPs
* Start the django server for tests `./manage.py runserver 0.0.0.0:8000`

SAML2 SPID compliant certificates
---------------------------------

Here an example about how to do that.

````
mkdir certificates && cd "$_"

spid-compliant-certificates generator \
    --key-size 3072 \
    --common-name "A.C.M.E" \
    --days 365 \
    --entity-id https://spid.acme.it \
    --locality-name Roma \
    --org-id "PA:IT-c_h501" \
    --org-name "A Company Making Everything" \
    --sector public \
    --key-out private.key \
    --crt-out public.cert

cd ../
````

Minimal SPID settings
---------------------

Instead of copy the whole demo project configuration you can add only the
necessary configuration entries (eg. SAML_CONFIG with 'organization' info,
and SPID_CONTACTS, other configurations that you want to be different from
defaults) directly to your project settings file. In this case don't
add `'spid_config'` to `settings.INSTALLED_APPS`.

An example of a minimal configuration for SPID is the following:

```python
SAML_CONFIG = {
    'entityid': 'https://your.spid.url/metadata',
    'organization': {
        'name': [('Example', 'it'), ('Example', 'en')],
        'display_name': [('Example', 'it'), ('Example', 'en')],
        'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')],
    },
}

SAML_USE_NAME_ID_AS_USERNAME = False
SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'username'
SAML_CREATE_UNKNOWN_USER = True
SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP = '__iexact'
SAML_ATTRIBUTE_MAPPING = {
    'spidCode': ('username', ),
    'email': ('email', ),
    'name': ('first_name', ),
    'familyName': ('last_name', ),
}

SPID_CONTACTS = [
    {
        'contact_type': 'other',
        'telephone_number': '+39 8475634785',
        'email_address': 'tech-info@example.org',
        'VATNumber': 'IT12345678901',
        'FiscalCode': 'XYZABCAAMGGJ000W',
        'Private': '',
    },
]
```

⚠️ In the example project, in `spid_settings.py` we found `disable_ssl_certificate_validation` set to True. This is only for test/development purpose and its usage means that the "remote metadata" won't validate the https certificates. That's something not intended for production environment, remote metadata must be avoided and the tls validation must be adopted.


Attribute Mapping
-----------------
Is necessary to maps SPID attributes to Django ones.
An example that links fiscalNumber wiht username have been configured in the example project.
This is another example that achieve the same behaviour without changing the default User model.

````
SAML_USE_NAME_ID_AS_USERNAME = False
SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'username'
SAML_CREATE_UNKNOWN_USER = True
SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP = '__iexact'

SAML_ATTRIBUTE_MAPPING = {
'fiscalNumber': ('username', ),
}
````

Download identity providers metadata
-----------------------------------

To update the list of entity providers use the custom django command `update_idps`.
In the example project you can do it as follows:

````
cd example/
python ./manage.py update_idps
````

Running tests (only for developers)
-----------------------------------

Tests are integrated into the demo project and are intended for use
only by developers.

To test the application:
````
pip install -r requirements-dev.txt
pip install -e .
python runtests.py
````

For running tests using the settings of the Demo project:
````
pip install -r requirements-dev.txt
cd example/
coverage erase
coverage run ./manage.py test djangosaml2_spid.tests
coverage report -m
````

Warnings
--------

- debug server uses the same SAML2 certificates, please create your SAML2 certificates for production and also a real TLS one for httpd!
- Read djangosaml2 documentation, remember to set SESSION_COOKIE_SECURE in your project settings.py
- The SPID Button template is only for test purpose, please don't use it in production, do your customizations instead!
- In a production environment please don't use "remote" as metadata storage, use "local" or "mdq" instead!
- When using spid-saml-check via docker image, mind that the metadata download url would match to `https://172.17.0.1:8000/spid/metadata` and not to localhost!

Authors
------------

- Giuseppe De Marco
- Davide Brunato

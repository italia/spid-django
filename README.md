SPID Django

![CI build](https://github.com/italia/spid-django/workflows/spid-django/badge.svg)
![Python version](https://img.shields.io/badge/license-Apache%202-blue.svg)
![License](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue.svg)


A SPID Service Provider based on [pysaml2](https://github.com/identitypython/pysaml2).


Introduction
------------

This is a Django application that provides a SAML2 Service Provider
for a Single Sign On with SPID, the Italian Digital Identity System.

This project comes with a demo on a Spid button template with both *spid-testenv2*
and *spid-saml-check* IDP preconfigured. See running the Demo project paragaph for details.

Furthermore, this application integrates the checks of
[Spid QA](https://www.spid.gov.it/assets/download/SPID_QAD.pdf)
within its CI pipeline, through [spid-sp-test](https://github.com/peppelinux/spid-sp-test).
See github actions log for details.

The technical documentation on SPID and SAML is available at [Docs Italia](https://docs.italia.it/italia/spid/spid-regole-tecniche)

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
This project uses **spid-saml-check** and **spid-testenv2** as
additional IDPs configured in a demo SPID button.

Prepare environment:
````
cd example/
virtualenv -ppython3 env
source env/bin/activate
pip install -r ../requirements.txt
````

Your example saml2 configuration is in `spid_config/spid_settings.py`.
See djangosaml2 and pysaml2 official docs for clarifications.

To run the demo project:
 - create the database `./manage.py migrate`
 - run `./manage.py runserver 0.0.0.0:8000`

or execute the run.sh script with these environment settings to enable tests idps:

 ````
 SPID_SAML_CHECK_REMOTE_METADATA_ACTIVE=True SPID_TESTENV2_REMOTE_METADATA_ACTIVE=True bash run.sh
 ````

If you choosed to use *spid-testenv2*, before starting it, you just have to save the
current demo metadata in *spid-testenv2* configuration, this way:

````
# cd into spid-testenv2/ base dir ...
wget http://localhost:8000/spid/metadata -O conf/sp_metadata.xml
````

Finally, start spid-testenv2 and spid-saml-check (docker is suggested) and
then open 'http://localhost:8000' in your browser.


Demo project with Docker
------------------------

To use Docker compose environment, add to /etc/hosts this line:
````
127.0.0.1	hostnet
````

then use `docker-compose --env-file docker-compose.env up` (the process takes some time) and when the services are up go to http://hostnet:8000/spid/login

**warning**: if you want to change ports of any of the docker-compose services (as, spid-testenv2, spid-saml-check) and/or the FQDN of the docker-compose default network gateway (defaults to `hostnet`) you need to change all the files
under `./example/configs/` to match the new configurations, changing only `./docker-compose.env` will not suffice.


Setup for an existing project
-----------------------------

djangosaml2_spid uses a pySAML2 fork.

* `pip install git+https://github.com/peppelinux/pysaml2.git@pplnx-v6.5.1`
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

Multiple ACS (new feature)
--------------------------
Current project allow to manage Service Provider metadata but with limitation to only one Assertion Consumer Service (or ACS) .

In case of metadata statically generated and validated positevely by AGID where there are multiple ACS, the assumption of index="0"
could result not correct.

Configuration, should allow to:
- to indicate which ACS id reference by current deploy: now it is work always as index="0"
- to create dinamically N nodes such as:
  - <md:KeyDescriptor use="signing">
  - <md:KeyDescriptor use="encryption">
  - <md:SingleLogoutService .../>
  - <md:AssertionConsumerService ... index="N" isDefault="true|false/>
  - <md:AttributeConsumingService index="N">

Pull request proposal (visible in example.spid_config.spid_settings) help to manage:
- service name (multiple languages)
- service description (multiple languages)
- list of attributes (does not matter if required or optional ones)
- multiple assertion_consumer_service
- mutiple single_logout_service
- multiple encryption_keypairs
```
SPID_CURRENT_INDEX: int = int(os.getenv("SPID_CURRENT_INDEX", "0"), 10)

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
    },     # index="0"
    {...}, # index="1"
]
assertion_consumer_service = [
    ('...', saml2.BINDING_HTTP_POST), # index="0"
    (f'{SPID_BASE_SCHEMA_HOST_PORT}/{SPID_ACS_URL_PATH}', saml2.BINDING_HTTP_POST), # index="1"
]

single_logout_service = [
    ('...', saml2.BINDING_HTTP_POST), # index="0"
    (f'{SPID_BASE_SCHEMA_HOST_PORT}/{SPID_SLO_POST_URL_PATH}', saml2.BINDING_HTTP_POST), # index="1"
]

encryption_keypairs = [{
    'key_file': '...', # index="0": not necessarily valid for runtime validation
    'cert_file': '...', # index="0": not necessarily valid for runtime validation
},{
    'key_file': SPID_PRIVATE_KEY, # index="1"
    'cert_file': SPID_PUBLIC_CERT, # index="1"
}]
```


Warnings
--------

- The SPID Button template is only for test purpose, please don't use it in production, do your customization instead!
- In a production environment please don't use "remote" as metadata storage, use "local" or "mdq" instead!

Authors
------------

Giuseppe De Marco

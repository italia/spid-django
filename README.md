> This Repository has been moved to [spid-django](https://github.com/italia/spid-django)

Djangosaml2 SPID
----------------

A SPID Service Provider based on [pysaml2](https://github.com/identitypython/pysaml2).


Introduction
------------
This is a Django application that provides a SAML2 Service Provider 
for a Single Sign On with SPID, the Italian Digital Identity System.

Technical documentation on SPID and SAML is available at [Docs Italia](https://docs.italia.it/italia/spid/spid-regole-tecniche/it/34.1.1/index.html)

![big picture](gallery/animated.gif)


Usage
-----

This project comes with a demo Spid button template with both *spid-testenv2* and *spid-saml-check* IDP preconfigured.
You just have to run the example project and put its metadata in spid-testenv2, this way:

````
wget http://localhost:8000/spid/metadata -O conf/djangosaml2_spid.xml
````

then define this entry in spid-testenv2/conf.


Dependencies
------------

- xmlsec
- python3-dev
- python3-pip
- libssl-dev 
- libsasl2-dev


Demo app
------------

Demo application uses **spid-saml-check** and **spid-testenv2** as 
SPID IDP, see `example/`.

Prepare environment
````
cd example/
virtualenv -ppython3 env
source env/bin/activate
pip install -r ../requirements.txt
````

Run the example project
 - Your example saml2 configuration is in `spid_config/spid_settings.py`. See djangosaml2 or pysaml2 official docs for clarifications
 - create demo database `./manage.py migrate`
 - run `./manage.py runserver 0.0.0.0:8000`
 - run spit-testenv2 and spid-saml-check (docker is suggested)
 - open 'http://localhost:8000'


Setup
------------

djangosaml2_spid uses a pySAML2 fork.

* `pip install git+https://github.com/peppelinux/pysaml2.git@pplnx-v6.5.1`
* `pip install git+https://github.com/italia/spid-django`
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
* Generate X.509 certificates and store them to a path, generally in `./certificates`
  `openssl req -nodes -new -x509 -newkey rsa:2048 -days 3650 -keyout certificates/private.key -out certificates/public.cert`
* Register the SP metadata to the your test Spid IDP
* Start the django server for tests `./manage.py runserver 0.0.0.0:8000`


Warnings
--------

- The SPID Button template is only for test purpose, please don't use it in production, do your customization instead!

Authors
------------

Giuseppe De Marco

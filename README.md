djangosaml2_spid
----------------

Django SAML2 Service Provider compliant to SPID Technical Requirements,
based on [pysaml2](https://github.com/identitypython/pysaml2).


Introduction
------------
This is a django application that provides a SAML2 Service Provider 
for a Single Sign On authentication through a SPID Identity Provider (SAML).

Technical documentation on SPID and SAML is available at:
https://github.com/italia/spid-docs

Demo app
------------
[Django-Identity](https://github.com/peppelinux/Django-Identity/tree/master/djangosaml2_sp)


Setup
------------

* Install djangosaml2_spid via pip in your virtualenv and add it to the project INSTALLED_APPS.
* Read `djangosaml2` official documentation, in particular [how to support SameSiteCookie](https://github.com/knaperek/djangosaml2#samesite-cookie)
* Add spid urls to your project url patterns, following djangosaml2 docs
* Copy `djangosaml2_spid/settings.py` to project's file, eg: _saml2_things_settings.py_, then import it in your project `settings`. This would be your SAML2 SP configuration.
* Generate X.509 certificates and store them somewhere
* Register your SP with the IdP with its metadata
* Start the django server for tests

Authors
------------

Giuseppe De Marco

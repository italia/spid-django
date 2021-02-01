djangosaml2_spid
----------------

Django SAML2 Service Provider compliant to SPID Technical Requirements,
based on [pysaml2](https://github.com/identitypython/pysaml2).


Introduction
------------
This is a django application that enable a SAML2 Service Provider, 
it enables a Single Sign On authentication through a SPID Identity Provider (SAML).

Technical documentation on SPID and SAML is available at:
https://github.com/italia/spid-docs and
https://github.com/umbros/spid-docs/blob/master/pages/documentazione-e-utilita.md

Demo app
------------
[Django-Identity](https://github.com/peppelinux/Django-Identity/tree/master/djangosaml2_sp)


Setup
------------

* Install djangosaml2_spid via pip in your virtualenv and add it to the project INSTALLED_APPS.
* Add spid urls to your project url patterns
* Change `djangosaml2_spid/settings.py` to a project _saml2_things_settings.py_ file and import it in your project `settings`.
* Generate X.509 certificates and store them somewhere
* Register your SP with the IdP.
* Start the app server

Authors
------------

Giuseppe De Marco

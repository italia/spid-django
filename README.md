# django-spid-demo
Demo of a SPID authentication for Django,
based on [python3-saml](https://github.com/onelogin/python3-saml).


# Introduction
This is a django project with one demo app, that shows how to use
Single Sign On authentication through a SPID Identity Provider (SAML).

Technical documentation on SPID and SAML is available at:
https://github.com/italia/spid-docs and
https://github.com/umbros/spid-docs/blob/master/pages/documentazione-e-utilita.md


# Installation

## General overview

* Install django-spid via pip in your virtualenv and add it to the project INSTALLED_APPS.
* Add spid urls to your project url patterns
* Generate X.509 certificates and store them somewhere
* Register your SP with the IdP.

* Change the ``saml/settings.json`` and ``saml/advanced_settings.json``
  configuration files using your metadata (only for test purpose).

* Start the app server


## Local development details

A **test identity provider** can be installed on your development environment
(your laptop?), following instructions at:
https://github.com/umbros/spid-docs/blob/master/pages/spid-ambiente-di-test.md

Here follows more detailed steps with some suggestions:

* choose a domain for your Service Provider (i.e. spid.yourdomain.it)

* generate self-signed certificates for your SP (you can do that here:
  https://developers.onelogin.com/saml/online-tools/x509-certs/obtain-self-signed-certs)

* put the content of the generated certificates under ``saml/certs/``
  (name them: sp.crt, sp.key and sp.csr; CSR is not useed here, I think)

* modify your /etc/hosts file, to redirect both
  ``spid-testenv-identityserver`` and ``spid.yourdomain.it`` to your ``localhost``
  ```
  echo "127.0.0.1 spid-testenv-identityserver" | sudo tee -a /etc/hosts
  ```

* start the dockerized service with
  ```
  docker-compose up
  ```

* visit https://spid-testenv-identityserver:8080, go to section
  **Service Provider**/**Creazione Metadata**

* fill in the form:
    * **Entity ID**: http://spid.yourdomain.it
    * **Certificate**: put the content of the sp.crt, with no
      headers in the text area
    * **Single Logout Service/Binding**: keep HTTP-POST
    * **Single Logout Service/Location**: http://spid.yourdomain.it/?sls
    * **Assertion consumer Service/Binding**: HTTP-POST is ok
    * **Assertion consumer Service/Location**:
      http://spid.yourdomain.it/?acs
    * **Attribute  Consuming Service**:
        * **Name and Description**: I don't get this, probably not
          needed, else `test/test` should be ok
        * choose all fields you want returned from the IdP to your
          app, you'll see them in the page returned after the
          user was logged in
    * **Organization**: this section can be left empty.

* pressing **Scarica** will not work as non-HTTPS urls will not validate,
  so, copy *the XML code* in the text area and save it to a
  ``metadata-yourdomain.xml`` file; that will be your SP's metadata

* press the **Salva** button, that will **register** the SP with the data
  you just inserted into the IdP.

* press the **Utenti** button and create a new user,
  only entering those fields that you want to see later;
  a note: in this interface new users cannot be modified, only deleted
  and re-created; that's ok, not everything can be perfect

# Useful debugging tools

- browser extensions to track SAML requests and response
  (they exist both for Chrome and Firefox)
- the "tools" tab within the ``carbon`` admin interface of the IdP
  (9443, admin/admin), that allows the verification of the requests.


# Execution

When the server is running, the home page shows a login button that
starts the SSO workflow.

Pressing the login button, a request is packed and sent to the IdP.

The IdP responds by redirecting you to its own login page.

You insert your credential (one of the user you just created)

The IdP redirects you to your SP, and a page with the attributes of the
signed in user is shown.

# TODOs

- improve session management

- improve user data storage

- tests
